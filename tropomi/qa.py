# tropomi/qa.py
# Purpose: Keep only pixels we trust using a QA threshold. (QA filtering; defaults to sensible behavior)
# Why: EO datasets include quality metrics; filtering avoids misleading stats/plots.

import numpy as np
import xarray as xr
from .io import no2_column, get_var

def qa_field(ds: xr.Dataset) -> xr.DataArray | np.ndarray:
    """
    Try common QA field names; fallback: mark valid where NO2 is finite.
    """
    candidates = ["qa_value", "qa_value_no2"]
    try:
        return get_var(ds, candidates)
    except KeyError:
        # Fallback behavior: if no QA is available, use finite NO2 as 'valid'
        return np.isfinite(no2_column(ds).values)

def valid_mask(ds: xr.Dataset, threshold: float = 0.75) -> xr.DataArray | np.ndarray:
    """
    Return a boolean mask of valid pixels where QA >= threshold.
    - If we only have a boolean fallback (np.ndarray), return it directly.
    """
    q = qa_field(ds)
    if isinstance(q, xr.DataArray):
        return q >= threshold
    return q  # already boolean ndarray
