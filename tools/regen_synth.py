# tools/regen_synth.py
from pathlib import Path

import numpy as np
import xarray as xr


def main() -> None:
    Path("tests/data").mkdir(parents=True, exist_ok=True)

    no2 = np.random.rand(32, 32).astype("float32") * 1e-5
    qa = np.ones((32, 32), dtype="float32")

    ds = xr.Dataset(
        {
            "nitrogendioxide_tropospheric_column": (("y", "x"), no2),
            "qa_value": (("y", "x"), qa),
        },
        coords={"y": np.arange(32), "x": np.arange(32)},
        attrs={"title": "synthetic tropomi-like no2"},
    )
    ds.to_netcdf("tests/data/synthetic.nc", engine="scipy")
    print("synthetic.nc ready (scipy)")


if __name__ == "__main__":
    main()
