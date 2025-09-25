# tropomi/render.py
# Purpose: Visual quicklook to 'see' the field after QA filtering. (quicklook PNG)
# Why: Quick visual validation is powerful and interviewers love demos.

from __future__ import annotations

import io
from typing import Sequence

import matplotlib.pyplot as plt
import xarray as xr

from .io import no2_column
from .qa import valid_mask


def quicklook_png(ds: xr.Dataset, qa_thresh: float = 0.75) -> bytes:
    """
    Render a simple heatmap PNG of the QA-filtered NO2 column.
    """
    arr = no2_column(ds).where(valid_mask(ds, qa_thresh)).values

    fig = plt.figure(figsize=(4, 4), dpi=150)
    ax = plt.gca()
    ax.imshow(arr, origin="upper")  # <-- no assignment
    ax.set_title("NO₂ quicklook")
    ax.set_axis_off()

    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def histogram_png(bin_edges: Sequence[float], counts: Sequence[int]) -> bytes:
    """
    Render a histogram (bins + counts) as a bar chart PNG.
    """
    fig = plt.figure(figsize=(4, 3), dpi=150)
    ax = plt.gca()

    # Convert edges->centers for a simple bar plot
    centers = []
    widths = []
    for i in range(len(bin_edges) - 1):
        a = bin_edges[i]
        b = bin_edges[i + 1]
        centers.append(0.5 * (a + b))
        widths.append(b - a)

    ax.bar(centers, counts, width=widths, align="center")
    ax.set_title("NO₂ histogram")
    ax.set_xlabel("NO₂ column")
    ax.set_ylabel("Count")

    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def tile_png(
    ds: xr.Dataset,
    y0: int,
    y1: int,
    x0: int,
    x1: int,
    qa_thresh: float = 0.75,
) -> bytes:
    """
    Render a cropped quicklook for the window [y0:y1, x0:x1] after QA filtering.
    """
    arr = no2_column(ds).where(valid_mask(ds, qa_thresh)).values
    h, w = arr.shape

    # Clamp ranges to image bounds
    y0 = max(0, min(h, y0))
    y1 = max(0, min(h, y1))
    x0 = max(0, min(w, x0))
    x1 = max(0, min(w, x1))
    if y1 <= y0 or x1 <= x0:
        raise ValueError("Invalid tile bounds")

    sub = arr[y0:y1, x0:x1]

    fig = plt.figure(figsize=(3, 3), dpi=150)
    ax = plt.gca()
    ax.imshow(sub, origin="upper")
    ax.set_axis_off()

    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    return buf.read()
