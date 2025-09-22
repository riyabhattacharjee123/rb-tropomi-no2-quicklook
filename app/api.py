# app/api.py
# Purpose: Expose a clean web API: /health, /info, /stats, /histogram, /quicklook, /histogram_png, /stats_csv, /metrics
# Why: EO microservice with QA filtering, visuals, and Prometheus metrics (cloud-friendly).

import io
import os
import time
import csv

import xarray as xr
from fastapi import FastAPI, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

# Prometheus metrics
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from tropomi.no2 import no2_stats, no2_histogram
from tropomi.render import quicklook_png, histogram_png as histogram_png_render

from app.db import init_db, engine
init_db()
from sqlalchemy import text as _sqltext


# -------- Settings --------
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
MAX_UPLOAD = int(os.getenv("MAX_UPLOAD", 20 * 1024 * 1024))  # 20 MB default

async def _read_small_file(file: UploadFile) -> bytes:
    """Read uploaded file and enforce a size guard to protect the service."""
    raw = await file.read()
    if len(raw) > MAX_UPLOAD:
        raise HTTPException(413, f"File too large (> {MAX_UPLOAD//1024//1024} MB)")
    return raw

def _open_ds(raw: bytes) -> xr.Dataset:
    """Open a NetCDF from bytes. Try SciPy (NetCDF3) first, then netCDF4 (HDF5)."""
    bio = io.BytesIO(raw)
    try:
        return xr.open_dataset(bio, engine="scipy")
    except Exception:
        bio.seek(0)
        return xr.open_dataset(bio, engine="netcdf4")

# -------- App --------
app = FastAPI(
    title="TROPOMI NO2 Quicklook & QA",
    version=APP_VERSION,
    description="Upload a TROPOMI-like NetCDF; get QA-filtered stats, histograms, quicklooks, and Prometheus metrics.",
)

# ---- Metrics (labels help break down by endpoint) ----
REQUESTS = Counter("api_requests_total", "Total API requests", ["endpoint"])
LATENCY = Histogram("api_request_latency_seconds", "Latency per request", ["endpoint"])
ERRORS  = Counter("api_errors_total", "API errors", ["endpoint"])

# -------- Models --------
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

# -------- Routes --------
@app.get("/health", tags=["ops"], summary="Liveness check")
def health():
    REQUESTS.labels("health").inc()
    return {"status": "ok"}

@app.get("/info", tags=["ops"], summary="Service info")
def info():
    REQUESTS.labels("info").inc()
    return {"name": app.title, "version": app.version, "about": "TROPOMI NO2 microservice with QA filtering & metrics"}

@app.get("/metrics", tags=["ops"], summary="Prometheus metrics")
def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

@app.post("/stats", response_model=StatsResponse, tags=["analysis"], summary="NO₂ stats (JSON)")
async def stats(file: UploadFile, qa: float = Query(0.75, ge=0.0, le=1.0)):
    endpoint = "stats"
    REQUESTS.labels(endpoint).inc()
    start = time.time()
    try:
        raw = await _read_small_file(file)
        ds = _open_ds(raw)
        result = no2_stats(ds, qa_thresh=qa)
        with engine.begin() as conn:
            conn.execute(_sqltext("""
            INSERT INTO stats (qa_threshold, count, min, mean, max)
            VALUES (:qa, :count, :min, :mean, :max)
            """), dict(qa=result["qa_threshold"], count=result["count"],
                    min=result["min"], mean=result["mean"], max=result["max"]))
        return JSONResponse(result)
    except Exception as e:
        ERRORS.labels(endpoint).inc()
        raise HTTPException(400, f"Failed to compute stats: {e}")
    finally:
        LATENCY.labels(endpoint).observe(time.time() - start)

@app.post("/histogram", response_model=HistogramResponse, tags=["analysis"], summary="NO₂ histogram (JSON)")
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
        return JSONResponse(result)
    except Exception as e:
        ERRORS.labels(endpoint).inc()
        raise HTTPException(400, f"Failed to compute histogram: {e}")
    finally:
        LATENCY.labels(endpoint).observe(time.time() - start)

@app.post("/quicklook", tags=["render"], summary="Quicklook PNG")
async def quicklook(file: UploadFile, qa: float = Query(0.75, ge=0.0, le=1.0)):
    endpoint = "quicklook"
    REQUESTS.labels(endpoint).inc()
    start = time.time()
    try:
        raw = await _read_small_file(file)
        ds = _open_ds(raw)
        png = quicklook_png(ds, qa_thresh=qa)
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
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(result.keys()))
        writer.writeheader()
        writer.writerow(result)
        return Response(
            content=buf.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=stats.csv"},
        )
    except Exception as e:
        ERRORS.labels(endpoint).inc()
        raise HTTPException(400, f"Failed to produce stats CSV: {e}")
    finally:
        LATENCY.labels(endpoint).observe(time.time() - start)
        
@app.get("/stats_recent", tags=["analysis"], summary="Recent stats from DB")
def stats_recent(limit: int = Query(10, ge=1, le=100)):
    with engine.begin() as conn:
        rows = conn.execute(_sqltext("""
          SELECT created_at, qa_threshold, count, min, mean, max
          FROM stats ORDER BY id DESC LIMIT :lim
        """), dict(lim=limit)).mappings().all()
    return {"items": [dict(r) for r in rows]}

