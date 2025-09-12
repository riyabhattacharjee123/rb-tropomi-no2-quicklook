# tropomi/render.py
# Purpose: Visual quicklook to 'see' the field after QA filtering. (quicklook PNG)
# Why: Quick visual validation is powerful and interviewers love demos.

import io
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from .io import no2_column
from .qa import valid_mask

def quicklook_png(ds: xr.Dataset, qa_thresh: float = 0.75) -> bytes:
    """
    Render an imshow PNG for valid NO2 pixels. Returns raw PNG bytes.
    """
    no2 = no2_column(ds)
    mask = valid_mask(ds, qa_thresh)
    arr = no2.where(mask).values

    fig = plt.figure(figsize=(4, 3), dpi=150)
    ax = plt.gca()
    im = ax.imshow(arr, origin="upper")
    ax.set_axis_off()
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Tropospheric NO₂")

    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format="png", bbox_inches=0, pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    return buf.read()

def histogram_png(bin_edges, counts) -> bytes:
    import io
    import numpy as np
    import matplotlib.pyplot as plt

    edges = np.array(bin_edges)
    centers = (edges[:-1] + edges[1:]) / 2.0
    width = (centers[1] - centers[0]) if len(centers) > 1 else 1.0

    fig = plt.figure(figsize=(4, 3), dpi=150)
    ax = plt.gca()
    ax.bar(centers, counts, width=width)
    ax.set_xlabel("Tropospheric NO₂")
    ax.set_ylabel("Count")
    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    return buf.read()

