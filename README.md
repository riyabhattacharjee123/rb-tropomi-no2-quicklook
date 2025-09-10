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
- **`/metrics`** – Prometheus metrics (request count, latency, errors)
- **`/health`** – container liveness probe
- **`/info`** – service metadata (name, version, about)

---

##  Project Structure

rb-tropomi-no2-quicklook/  
├── app/ # FastAPI entrypoint  
│ └── api.py  
├── tropomi/ # EO processing modules  
│ ├── io.py  
│ ├── qa.py  
│ ├── no2.py  
│ └── render.py  
├── tests/ # pytest + synthetic data  
│ ├── conftest.py  
│ ├── test_synthetic.py  
│ └── data/  
├── tools/ # utilities  
│ └── regen_synth.py  
├── requirements.txt # pinned dependencies  
├── Dockerfile # container build  
├── Makefile # developer shortcuts  
└── README.md  


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
make run
```

### 3. Endpoints (example curl)
```bash
# Stats
curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/stats?qa=0.75"

# Histogram
curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/histogram?qa=0.75&bins=12"

# Quicklook (PNG saved to file)
curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/quicklook?qa=0.75" -o quicklook.png

# Metrics
curl "http://localhost:8000/metrics" | head

# Interactive docs
open http://localhost:8000/docs   # Swagger UI
open http://localhost:8000/redoc  # ReDoc
```

#### Example Output
Stats
```
{
  "count": 1024,
  "min": 4.22e-09,
  "mean": 4.85e-06,
  "max": 9.99e-06,
  "qa_threshold": 0.75
}
```

Histogram
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

- Uses synthetic NetCDF (tests/data/synthetic.nc) for fast, portable CI.

- Pure-Python SciPy engine → no native library headaches.

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

- Follow clean DevOps workflows

- Perfect for learning, and as a template for larger EO pipelines.

## Roadmap

- Add /histogram_png endpoint (matplotlib bar plot)

- Add /stats_csv endpoint for CSV downloads

- Batch ingestion pipeline with Airflow

- Deploy demo on Dask-Gateway or HTCondor

- Grafana dashboard for NO₂ trends

### License

MIT — feel free to reuse and extend.




