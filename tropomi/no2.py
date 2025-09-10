# tropomi/no2.py
# Purpose: Compute descriptive statistics + histogram for NO2 over valid pixels.
# Why: Adds analytical value.

import numpy as np
import xarray as xr
from .io import no2_column
from .qa import valid_mask

def no2_stats(ds: xr.Dataset, qa_thresh: float = 0.75) -> dict:
    """
    Compute count/min/mean/max on QA-screened NO2.
    """
    no2 = no2_column(ds)
    mask = valid_mask(ds, threshold=qa_thresh)
    s = no2.where(mask)
    arr = s.values  # N-D array (likely 2-D for a single swath)
    return {
        "count": int(np.isfinite(arr).sum()),
        "min": float(np.nanmin(arr)),
        "mean": float(np.nanmean(arr)),
        "max": float(np.nanmax(arr)),
        "qa_threshold": qa_thresh,
    }

def no2_histogram(ds: xr.Dataset, qa_thresh: float = 0.75, bins: int = 20) -> dict:
    """
    Compute a simple histogram (bin_edges + counts) for valid NO2 pixels.
    Why: Extra feature for dashboards/QA analysis.
    """
    no2 = no2_column(ds)
    mask = valid_mask(ds, threshold=qa_thresh)
    arr = no2.where(mask).values
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        edges = np.linspace(0, 1e-4, bins + 1)  # sensible default if empty
        counts = np.zeros(bins, dtype=int)
    else:
        counts, edges = np.histogram(arr, bins=bins)
    return {
        "qa_threshold": qa_thresh,
        "bins": bins,
        "bin_edges": edges.tolist(),
        "counts": counts.tolist(),
    }
