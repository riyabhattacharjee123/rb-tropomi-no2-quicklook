# tropomi/io.py
# Purpose: Opening datasets safely + finding the right variable names.
# Why: EO product variables sometimes differ across versions. We code defensively.

from __future__ import annotations

import xarray as xr


def open_netcdf(path_or_buffer) -> xr.Dataset:
    """
    Open a TROPOMI NO2 NetCDF/HDF5 dataset.
    - Accepts a filesystem path (str) OR a file-like buffer (BytesIO).
    - xr.open_dataset defers loading; we only read metadata until we access .values
    """
    return xr.open_dataset(path_or_buffer)


def get_var(ds: xr.Dataset, candidates: list[str]) -> xr.DataArray:
    """
    Return the first variable that exists in the dataset from a list of possible names.
    Why: Product versions may rename variables; this makes our code robust.
    """
    for name in candidates:
        if name in ds.variables:
            return ds[name]
    raise KeyError(f"None of {candidates} found in dataset")


def no2_column(ds: xr.Dataset) -> xr.DataArray:
    """
    TROPOMI tropospheric NO2 column candidates (examples; varies by product version).
    """
    return get_var(
        ds,
        [
            "nitrogendioxide_tropospheric_column",
            "no2_tropospheric_column",
            "tropospheric_NO2_column",
        ],
    )
