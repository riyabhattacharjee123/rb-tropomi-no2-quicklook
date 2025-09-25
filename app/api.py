# app/api.py
# ------------------------------------------------------------------------------
# Purpose
# -------
# Expose a cloud-friendly FastAPI microservice for TROPOMI-like NO₂ files:
# - Upload NetCDF → get:
#     • /stats (JSON)
#     • /histogram (JSON)
#     • /quicklook (PNG)
#     • /histogram_png (PNG)
#     • /stats_csv (CSV)
#     • /tile_png (PNG subwindow)
# - Observability:
#     • /metrics (Prometheus text format)
#     • /health, /info
#
# Why this design?
# - Clean, composable microservice with endpoints that recruiters can try instantly.
# - File-size guard + NetCDF engine fallback for robustness.
# - Prometheus metrics for production-like monitoring.
# - CORS enabled so a small browser page can upload files directly.
# - Optional SQLite persistence showing you can store results and query them back.
# ------------------------------------------------------------------------------

from __future__ import annotations

import csv

# ---- Standard libs
import io
import json
import logging
import os
import sys
import time

# ---- Third-party libs
import xarray as xr
from fastapi import FastAPI, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel
from sqlalchemy import text as _sqltext  # used for simple inserts/selects

# ---- Local DB helper (SQLite by default)
from app.db import engine, init_db

# ---- Our EO logic (you created these modules)
from tropomi.no2 import no2_histogram, no2_stats
from tropomi.render import histogram_png as histogram_png_render
from tropomi.render import quicklook_png, tile_png

# ==============================================================================
# Settings & App setup
# ==============================================================================

# Version & safety limit for uploads (can be set via Docker/Compose env)
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
MAX_UPLOAD = int(os.getenv("MAX_UPLOAD", 20 * 1024 * 1024))  # 20 MB

# Basic JSON-style logging to stdout (friendly for containers/Grafana/Loki)
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")
log = logging.getLogger("api")


def log_event(event: str, **fields) -> None:
    """Small helper to emit JSON logs: log_event("stats_done", count=1024)."""
    payload = {"event": event, **fields}
    log.info(json.dumps(payload))


# Create the FastAPI app with helpful metadata
app = FastAPI(
    title="TROPOMI NO2 Quicklook & QA",
    version=APP_VERSION,
    description=(
        "Upload a TROPOMI-like NetCDF (e.g., synthetic test file). "
        "Get QA-filtered stats, histograms, quicklooks, metrics, and recent stats from SQLite."
    ),
)

# Enable CORS so a simple HTML page can POST a file from the browser.
# For production, restrict allow_origins to your domain(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # DEMO-ONLY; tighten in production
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize local DB (creates table if missing)
init_db()

# Prometheus counters/histograms (labeled per-endpoint)
REQUESTS = Counter("api_requests_total", "Total API requests", ["endpoint"])
LATENCY = Histogram("api_request_latency_seconds", "Latency per request", ["endpoint"])
ERRORS = Counter("api_errors_total", "API errors", ["endpoint"])

# ==============================================================================
# Pydantic response models (for clean OpenAPI docs)
# ==============================================================================


class StatsResponse(BaseModel):
    count: int
    min: float
    mean: float
    max: float
    qa_threshold: float


class HistogramResponse(BaseModel):
    qa_threshold: float
    bins: int
    bin_edges: list[float]
    counts: list[int]


# ==============================================================================
# Internal helpers (safety & robustness)
# ==============================================================================


async def _read_small_file(file: UploadFile) -> bytes:
    """
    Read uploaded file into memory and enforce a size limit.
    Why: Avoids someone uploading huge files that would crash the container.
    """
    raw = await file.read()
    if len(raw) > MAX_UPLOAD:
        raise HTTPException(413, f"File too large (> {MAX_UPLOAD//1024//1024} MB)")
    return raw


def _open_ds(raw: bytes) -> xr.Dataset:
    """
    Open a NetCDF file from raw bytes, trying the SciPy engine first (NetCDF3),
    then falling back to netCDF4 (HDF5-based) if needed.
    Why: Different NetCDF formats require different backends; this makes it "just work".
    """
    bio = io.BytesIO(raw)
    try:
        return xr.open_dataset(bio, engine="scipy")
    except Exception:
        bio.seek(0)
        return xr.open_dataset(bio, engine="netcdf4")


# ==============================================================================
# Basic ops endpoints
# ==============================================================================


@app.get("/health", tags=["ops"], summary="Liveness check")
def health():
    REQUESTS.labels("health").inc()
    return {"status": "ok"}


@app.get("/info", tags=["ops"], summary="Service info")
def info():
    REQUESTS.labels("info").inc()
    return {
        "name": app.title,
        "version": app.version,
        "about": "TROPOMI NO2 microservice with QA filtering, metrics, and optional SQLite persistence",
    }


@app.get("/metrics", tags=["ops"], summary="Prometheus metrics")
def metrics():
    """
    Exposes counters and histograms in Prometheus format so Prometheus/Grafana can scrape and visualize.
    """
    # No endpoint label here (Prometheus scrapes this a lot)
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


# ==============================================================================
# Analysis endpoints
# ==============================================================================


@app.post("/stats", response_model=StatsResponse, tags=["analysis"], summary="NO₂ stats (JSON)")
async def stats(file: UploadFile, qa: float = Query(0.75, ge=0.0, le=1.0)):
    endpoint = "stats"
    REQUESTS.labels(endpoint).inc()
    start = time.time()
    try:
        # Safety + open
        raw = await _read_small_file(file)
        ds = _open_ds(raw)

        # Compute stats
        result = no2_stats(ds, qa_thresh=qa)

        # Persist a row (SQLite) so we can query recent results later
        with engine.begin() as conn:
            conn.execute(
                _sqltext(
                    """
                    INSERT INTO stats (qa_threshold, count, min, mean, max)
                    VALUES (:qa, :count, :min, :mean, :max)
                    """
                ),
                dict(
                    qa=result["qa_threshold"],
                    count=result["count"],
                    min=result["min"],
                    mean=result["mean"],
                    max=result["max"],
                ),
            )

        log_event("stats_done", count=result["count"], mean=result["mean"], qa=qa)
        return JSONResponse(result)

    except Exception as e:
        ERRORS.labels(endpoint).inc()
        # Tip: In production you might hide raw exception details
        raise HTTPException(400, f"Failed to compute stats: {e}")
    finally:
        LATENCY.labels(endpoint).observe(time.time() - start)


@app.post(
    "/histogram",
    response_model=HistogramResponse,
    tags=["analysis"],
    summary="NO₂ histogram (JSON)",
)
async def histogram(
    file: UploadFile,
    qa: float = Query(0.75, ge=0.0, le=1.0),
    bins: int = Query(20, ge=5, le=200),
):
    endpoint = "histogram"
    REQUESTS.labels(endpoint).inc()
    start = time.time()
    try:
        raw = await _read_small_file(file)
        ds = _open_ds(raw)

        result = no2_histogram(ds, qa_thresh=qa, bins=bins)
        log_event("histogram_done", bins=bins, qa=qa)
        return JSONResponse(result)

    except Exception as e:
        ERRORS.labels(endpoint).inc()
        raise HTTPException(400, f"Failed to compute histogram: {e}")
    finally:
        LATENCY.labels(endpoint).observe(time.time() - start)


# ==============================================================================
# Rendering endpoints (PNGs & CSV)
# ==============================================================================


@app.post("/quicklook", tags=["render"], summary="Quicklook PNG")
async def quicklook(file: UploadFile, qa: float = Query(0.75, ge=0.0, le=1.0)):
    endpoint = "quicklook"
    REQUESTS.labels(endpoint).inc()
    start = time.time()
    try:
        raw = await _read_small_file(file)
        ds = _open_ds(raw)

        png = quicklook_png(ds, qa_thresh=qa)
        log_event("quicklook_done", qa=qa, size=len(png))
        return Response(content=png, media_type="image/png")

    except Exception as e:
        ERRORS.labels(endpoint).inc()
        raise HTTPException(400, f"Failed to render quicklook: {e}")
    finally:
        LATENCY.labels(endpoint).observe(time.time() - start)


@app.post("/histogram_png", tags=["render"], summary="Histogram as PNG")
async def histogram_png_endpoint(
    file: UploadFile,
    qa: float = Query(0.75, ge=0.0, le=1.0),
    bins: int = Query(20, ge=5, le=200),
):
    endpoint = "histogram_png"
    REQUESTS.labels(endpoint).inc()
    start = time.time()
    try:
        raw = await _read_small_file(file)
        ds = _open_ds(raw)

        h = no2_histogram(ds, qa_thresh=qa, bins=bins)
        png = histogram_png_render(h["bin_edges"], h["counts"])
        log_event("histogram_png_done", qa=qa, bins=bins, size=len(png))
        return Response(content=png, media_type="image/png")

    except Exception as e:
        ERRORS.labels(endpoint).inc()
        raise HTTPException(400, f"Failed to render histogram PNG: {e}")
    finally:
        LATENCY.labels(endpoint).observe(time.time() - start)


@app.post("/stats_csv", tags=["analysis"], summary="NO₂ stats as CSV")
async def stats_csv(file: UploadFile, qa: float = Query(0.75, ge=0.0, le=1.0)):
    endpoint = "stats_csv"
    REQUESTS.labels(endpoint).inc()
    start = time.time()
    try:
        raw = await _read_small_file(file)
        ds = _open_ds(raw)

        result = no2_stats(ds, qa_thresh=qa)

        # Construct a CSV in-memory (one header row + one data row)
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(result.keys()))
        writer.writeheader()
        writer.writerow(result)
        csv_bytes = buf.getvalue()

        log_event("stats_csv_done", qa=qa, bytes=len(csv_bytes))
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=stats.csv"},
        )

    except Exception as e:
        ERRORS.labels(endpoint).inc()
        raise HTTPException(400, f"Failed to produce stats CSV: {e}")
    finally:
        LATENCY.labels(endpoint).observe(time.time() - start)


@app.post("/tile_png", tags=["render"], summary="Cropped quicklook tile as PNG")
async def tile_png_endpoint(
    file: UploadFile,
    y0: int = Query(0, ge=0),
    y1: int = Query(16, ge=1),
    x0: int = Query(0, ge=0),
    x1: int = Query(16, ge=1),
    qa: float = Query(0.75, ge=0.0, le=1.0),
):
    """
    Returns a PNG for the subwindow [y0:y1, x0:x1] after QA filtering.
    Why: demonstrates a "map tile"-like capability useful in EO apps.
    """
    endpoint = "tile_png"
    REQUESTS.labels(endpoint).inc()
    start = time.time()
    try:
        raw = await _read_small_file(file)
        ds = _open_ds(raw)

        png = tile_png(ds, y0=y0, y1=y1, x0=x0, x1=x1, qa_thresh=qa)
        log_event("tile_png_done", qa=qa, y0=y0, y1=y1, x0=x0, x1=x1, size=len(png))
        return Response(content=png, media_type="image/png")

    except Exception as e:
        ERRORS.labels(endpoint).inc()
        raise HTTPException(400, f"Failed to render tile: {e}")
    finally:
        LATENCY.labels(endpoint).observe(time.time() - start)


# ==============================================================================
# Persistence read-back (from SQLite)
# ==============================================================================


@app.get("/stats_recent", tags=["analysis"], summary="Recent stats from DB")
def stats_recent(limit: int = Query(10, ge=1, le=100)):
    """
    Returns the most recent computed stats from the SQLite DB.
    Why: showcases simple persistence + a read API endpoint.
    """
    endpoint = "stats_recent"
    REQUESTS.labels(endpoint).inc()
    start = time.time()
    try:
        with engine.begin() as conn:
            rows = (
                conn.execute(
                    _sqltext(
                        """
                    SELECT created_at, qa_threshold, count, min, mean, max
                    FROM stats
                    ORDER BY id DESC
                    LIMIT :lim
                    """
                    ),
                    dict(lim=limit),
                )
                .mappings()
                .all()
            )
        return {"items": [dict(r) for r in rows]}
    except Exception as e:
        ERRORS.labels(endpoint).inc()
        raise HTTPException(400, f"Failed to read recent stats: {e}")
    finally:
        LATENCY.labels(endpoint).observe(time.time() - start)
