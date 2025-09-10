# tests/conftest.py
# - Ensures project root is importable
# - Ensures tests/data/synthetic.nc exists (pure-Python SciPy NetCDF)
# - This runs before tests collect, so the file will exist every time—locally and in CI.

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Auto-materialize the synthetic test file before test collection
def pytest_configure(config):
    import numpy as np
    import xarray as xr

    data_dir = os.path.join(PROJECT_ROOT, "tests", "data")
    os.makedirs(data_dir, exist_ok=True)
    nc_path = os.path.join(data_dir, "synthetic.nc")

    if not os.path.exists(nc_path):
        # Tiny, plausible NO2 field with QA=1 everywhere
        no2 = (np.random.rand(32, 32).astype("float32") * 1e-5)
        qa = np.ones((32, 32), dtype="float32")
        ds = xr.Dataset(
            {
                "nitrogendioxide_tropospheric_column": (("y", "x"), no2),
                "qa_value": (("y", "x"), qa),
            },
            coords={"y": np.arange(32), "x": np.arange(32)},
            attrs={"title": "synthetic tropomi-like no2"},
        )
        # Write via SciPy engine → avoids native deps (fast & portable)
        ds.to_netcdf(nc_path, engine="scipy")
        print(f"[tests] Created synthetic dataset at {nc_path}")
