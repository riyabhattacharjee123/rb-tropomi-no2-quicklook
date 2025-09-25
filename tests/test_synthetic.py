# tests/test_synthetic.py
# Purpose: Make CI reliable without downloading huge files.

from tropomi.io import open_netcdf
from tropomi.no2 import no2_histogram, no2_stats
from tropomi.render import quicklook_png


def test_stats_hist_quicklook():
    ds = open_netcdf("tests/data/synthetic.nc")
    stats = no2_stats(ds, qa_thresh=0.75)
    assert stats["count"] > 0
    assert stats["min"] >= 0.0
    assert stats["max"] < 1e-4

    hist = no2_histogram(ds, qa_thresh=0.75, bins=10)
    assert hist["bins"] == 10
    assert len(hist["bin_edges"]) == 11
    assert len(hist["counts"]) == 10

    png = quicklook_png(ds, qa_thresh=0.75)
    assert isinstance(png, (bytes, bytearray))
    assert len(png) > 500  # should be non-trivial image
