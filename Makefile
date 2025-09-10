# Makefile — common dev tasks for tropomi-no2-quicklook
# Usage: `make help`

# ---- Config (edit these if you like) ----
IMAGE_NAME := tropomi-no2
TAG        := dev
PORT       := 8000

# ---- Phony targets (not files) ----
.PHONY: help setup test regen-synth build run clean docker-clean lint format

help:
	@echo "Available targets:"
	@echo "  make setup        - Install/upgrade pip and project requirements"
	@echo "  make test         - Run pytest with local PYTHONPATH"
	@echo "  make regen-synth  - Recreate tests/data/synthetic.nc (SciPy engine)"
	@echo "  make build        - Build Docker image $${IMAGE_NAME}:$${TAG}"
	@echo "  make run          - Run container on port $${PORT}"
	@echo "  make clean        - Remove __pycache__ and pytest caches"
	@echo "  make docker-clean - Remove dangling Docker images"
	@echo "  make lint         - (optional) Run flake8 if installed"
	@echo "  make format       - (optional) Run black if installed"

setup:
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt

test:
	PYTHONPATH=. pytest -q

regen-synth:
	python tools/regen_synth.py

build:
	docker build -t $(IMAGE_NAME):$(TAG) .

run:
	docker run --rm -p $(PORT):8000 $(IMAGE_NAME):$(TAG)

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} \; || true
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} \; || true

docker-clean:
	docker image prune -f

# Optional: only runs if tools are installed in your env
lint:
	@command -v flake8 >/dev/null 2>&1 || { echo "flake8 not installed; skipping"; exit 0; }
	flake8 app tropomi tests

format:
	@command -v black >/dev/null 2>&1 || { echo "black not installed; skipping"; exit 0; }
	black app tropomi tests
