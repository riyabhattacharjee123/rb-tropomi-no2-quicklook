# app/api.py
# Purpose: Expose a clean web API: /health, /stats, /quicklook, /histogram, /metrics, /info
# Why: Microservice architecture; metrics make it production-friendly and distinct.

import io
import time
from typing import Any

import xarray as xr
from fastapi import FastAPI, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

# Prometheus metrics (extra feature)
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from tropomi.no2 import no2_stats, no2_histogram
from tropomi.render import quicklook_png

app = FastAPI(title="TROPOMI NO2 Quicklook & QA", version="0.1.0")

# ---- Metrics (labels help break down by endpoint) ----
REQUESTS = Counter("api_requests_total", "Total API requests", ["endpoint"])
LATENCY = Histogram("api_request_latency_seconds", "Latency per request", ["endpoint"])
ERRORS  = Counter("api_errors_total", "API errors", ["endpoint"])

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

@app.get("/health")
def health():
    """Liveness check for containers/load balancers/traefik."""
    REQUESTS.labels("health").inc()
    return {"status": "ok"}

@app.get("/info")
def info():
    """Meta info for debugging and demos."""
    REQUESTS.labels("info").inc()
    return {"name": app.title, "version": app.version, "about": "TROPOMI NO2 microservice with QA filtering & metrics"}

@app.get("/metrics")
def metrics():
    """Prometheus scrape endpoint (Grafana can visualize)."""
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

@app.post("/stats", response_model=StatsResponse)
async def stats(file: UploadFile, qa: float = Query(0.75, ge=0.0, le=1.0)):
    endpoint = "stats"
    REQUESTS.labels(endpoint).inc()
    start = time.time()
    try:
        raw = await file.read()  # small files only; for large files stream to temp
        ds = xr.open_dataset(io.BytesIO(raw))
        result = no2_stats(ds, qa_thresh=qa)
        return JSONResponse(result)
    except Exception as e:
        ERRORS.labels(endpoint).inc()
        raise HTTPException(400, f"Failed to compute stats: {e}")
    finally:
        LATENCY.labels(endpoint).observe(time.time() - start)

@app.post("/histogram", response_model=HistogramResponse)
async def histogram(
    file: UploadFile,
    qa: float = Query(0.75, ge=0.0, le=1.0),
    bins: int = Query(20, ge=5, le=200),
):
    endpoint = "histogram"
    REQUESTS.labels(endpoint).inc()
    start = time.time()
    try:
        raw = await file.read()
        ds = xr.open_dataset(io.BytesIO(raw))
        result = no2_histogram(ds, qa_thresh=qa, bins=bins)
        return JSONResponse(result)
    except Exception as e:
        ERRORS.labels(endpoint).inc()
        raise HTTPException(400, f"Failed to compute histogram: {e}")
    finally:
        LATENCY.labels(endpoint).observe(time.time() - start)

@app.post("/quicklook")
async def quicklook(file: UploadFile, qa: float = Query(0.75, ge=0.0, le=1.0)):
    endpoint = "quicklook"
    REQUESTS.labels(endpoint).inc()
    start = time.time()
    try:
        raw = await file.read()
        ds = xr.open_dataset(io.BytesIO(raw))
        png = quicklook_png(ds, qa_thresh=qa)
        return Response(content=png, media_type="image/png")
    except Exception as e:
        ERRORS.labels(endpoint).inc()
        raise HTTPException(400, f"Failed to render quicklook: {e}")
    finally:
        LATENCY.labels(endpoint).observe(time.time() - start)
