# tests/test_db_recent.py
import os
import json
import subprocess
from pathlib import Path

def test_stats_recent_roundtrip():
    # Ensure synthetic file exists
    p = Path("tests/data/synthetic.nc")
    assert p.exists(), "Run: python tools/regen_synth.py"

    # Start app container for a quick integration test (ephemeral)
    # If your local app is already running, you can skip this and just curl localhost:8000
    # Here we use uvicorn directly for speed in CI-like run:
    import uvicorn, threading
    from app.api import app

    server = threading.Thread(
        target=uvicorn.run,
        kwargs=dict(app=app, host="127.0.0.1", port=9000, log_level="warning"),
        daemon=True,
    )
    server.start()

    import time, requests
    time.sleep(0.8)  # give server a moment

    # 1) POST /stats (writes to DB)
    files = {"file": p.open("rb")}
    r = requests.post("http://127.0.0.1:9000/stats?qa=0.75", files=files, timeout=5)
    assert r.ok, r.text
    data = r.json()
    assert "count" in data and data["count"] > 0

    # 2) GET /stats_recent
    r = requests.get("http://127.0.0.1:9000/stats_recent?limit=3", timeout=5)
    assert r.ok, r.text
    out = r.json()
    assert "items" in out and len(out["items"]) >= 1
