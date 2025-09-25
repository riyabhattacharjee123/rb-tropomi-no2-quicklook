# 🌍 TROPOMI NO₂ Quicklook & QA Microservice

[![CI](https://github.com/riyabhattacharjee123/rb-tropomi-no2-quicklook/actions/workflows/ci.yml/badge.svg)](https://github.com/riyabhattacharjee123/rb-tropomi-no2-quicklook/actions)

A lightweight **FastAPI microservice** for processing synthetic or real **TROPOMI Sentinel-5P NO₂ data**.  
It demonstrates cloud-native Earth Observation (EO) data pipelines with:

- ✅ **FastAPI** REST endpoints
- ✅ **xarray** + **NumPy** for NO₂ stats & histograms
- ✅ **Matplotlib** quicklook PNGs
- ✅ **Prometheus metrics** (ready for Grafana)
- ✅ **Dockerized** for cloud/HPC portability
- ✅ **Makefile workflow** for developer productivity
- ✅ **CI-ready** with synthetic NetCDF test data

---

##  Features

- **`/stats`** – compute count, min, mean, max (with QA filtering)  
- **`/histogram`** – compute histogram bins + counts  
- **`/quicklook`** – generate a PNG heatmap of NO₂  
- **`/histogram_png`** – histogram as a PNG bar plot  
- **`/stats_csv`** – download stats as CSV  
- **`/tile_png`** – return cropped tile PNG (like map tiles)  
- **`/stats_recent`** – read back recent stats from SQLite DB  
- **`/metrics`** – Prometheus metrics (request count, latency, errors)  
- **`/health`** – container liveness probe  
- **`/info`** – service metadata (name, version, about)

---

##  Project Structure

rb-tropomi-no2-quicklook/  
├── app/ # FastAPI entrypoint + DB 
│ └── api.py  
│ └── db.py  
├── tropomi/ # EO processing modules  
│ ├── io.py  
│ ├── qa.py  
│ ├── no2.py  
│ └── render.py  
├── tests/ # pytest + synthetic data  
│ ├── conftest.py  
│ ├── test_synthetic.py  
│ ├── test_db_recent.py  
│ └── data/  
├── tools/ # utilities  
│ └── regen_synth.py  
│ └── test_client.html  
├── requirements.txt # pinned dependencies  
├── Dockerfile # container build  
├── Makefile # developer shortcuts  
└── README.md  
├── Makefile # developer shortcuts  
└── .github  # CI/CD pipeline  
│ ├── workflows  
|   ├── ci.yml  
└── grafana  # example dashboards  
│ ├── dashboards  
|   ├── no2-overview.json  
├── prometheus.yml  # Prometheus scrape config  
├── compose.yml  # Prometheus + Grafana stack  
├── requirements.txt  # pinned dependencies  
├── Makefile  # developer shortcuts  
├── Dockerfile  # container build  
├── README.md  
└── bash_run_1.sh  



---

##  Setup & Usage

### 1. Local development (Codespaces or host)
```bash
make setup         # install deps
make regen-synth   # generate synthetic.nc for tests
make test          # run pytest
```

### 2. Docker build & run
```bash
make build
APP_VERSION=$(git rev-parse --short HEAD) make run
```

### 3. Endpoints (example curl)
```bash
# Stats (JSON)
curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/stats?qa=0.75"

# Histogram (JSON)
curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/histogram?qa=0.75&bins=12"

# Quicklook (PNG saved to file)
curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/quicklook?qa=0.75" -o quicklook.png
curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/histogram_png?qa=0.75&bins=12" -o hist.png

# CSV: summary stats
curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/stats_csv?qa=0.75" -o stats.csv

# Cropped tile (subwindow PNG)
curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/tile_png?y0=0&y1=16&x0=0&x1=16&qa=0.75" -o tile.png

# Recent stats from DB
curl "http://localhost:8000/stats_recent?limit=5"

# Metrics
curl "http://localhost:8000/metrics" | head

# Interactive docs
open http://localhost:8000/docs   # Swagger UI
open http://localhost:8000/redoc  # ReDoc
```

#### Example Output
Stats JSON
```
{
  "count": 1024,
  "min": 4.22e-09,
  "mean": 4.85e-06,
  "max": 9.99e-06,
  "qa_threshold": 0.75
}
```

Histogram JSON
```
{
  "qa_threshold": 0.75,
  "bins": 12,
  "bin_edges": [...],
  "counts": [...]
}
```

Quicklook  
Generated PNG example (quicklook.png):

#### Configuration

Environment variables:

`APP_VERSION` – shown in `/info` (set from git short SHA in dev)

`MAX_UPLOAD` – max upload size in bytes (default: 20 MB)


#### Developer Workflow (Makefile)
```bash
# Command	Description
make setup	#Install dependencies
make regen-synth	#Generate synthetic NetCDF test file
make test	#Run pytest
make build	#Build Docker image
make run	#Run container (port 8000 → FastAPI)
make clean	#Remove caches (pycache, pytest)
make docker-clean	#Prune dangling Docker images
make lint	#Run flake8 (if installed)
make format	#Run black (if installed)
```
### 4. Testing

- Uses synthetic NetCDF `tests/data/synthetic.nc` for fast, portable CI.

- Pure-Python SciPy engine → no native library issues.

- CI pipeline (GitHub Actions) runs:

  - install deps

  - generate synthetic file

  - run pytest

  - build Docker image

### 5. Deployment Ideas

- Deploy on Kubernetes or Docker Swarm with Traefik ingress.

- Wire Prometheus → Grafana dashboards for NO₂ stats/histograms.

- Extend with Airflow DAGs to batch-process EO files.

- Ingest real Sentinel-5P L2 NO₂ NetCDFs (swap synthetic data for ESA downloads).

## Why This Project

This repo is part of my cloud + DevOps + EO learning journey.
It shows how to:

- Build EO-specific APIs with FastAPI

- Use xarray for satellite data analysis

- Containerize with Docker

- Add CI/CD pipelines

- Expose metrics for monitoring

- Persist results in SQLite (extendable to Postgres/Cloud DBs)

- Follow clean DevOps workflows

- Perfect for learning, and as a template for larger EO pipelines.

###  Run from GHCR

```bash
docker pull ghcr.io/riyabhattacharjee123/tropomi-no2-quicklook:latest
docker run --rm -p 8000:8000 \
  -e APP_VERSION=$(date +%Y%m%d%H%M) \
  ghcr.io/riyabhattacharjee123/tropomi-no2-quicklook:latest
```

Open in web browser:  
`https://scaling-garbanzo-v5q4w4jv5jr3wj5v-8000.app.github.dev/docs`  
and  
`https://scaling-garbanzo-v5q4w4jv5jr3wj5v-8000.app.github.dev/metrics`  

Quick cURL tests (from another terminal tab while the container runs):

```bash
# JSON
curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/stats?qa=0.75"

curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/histogram?qa=0.75&bins=12"

# PNGs
curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/quicklook?qa=0.75" -o quicklook.png

curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/histogram_png?qa=0.75&bins=12" -o hist.png

# CSV
curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/stats_csv?qa=0.75" -o stats.csv
```


## Roadmap

- Add `/histogram_png` endpoint (matplotlib bar plot)

- Add `/stats_csv` endpoint for CSV downloads

- SQLite persistence + `/stats_recent`

- Batch ingestion pipeline with Airflow

- Deploy demo on Dask-Gateway or HTCondor

- Grafana dashboard for NO₂ trends

### License

MIT — feel free to reuse and extend.




