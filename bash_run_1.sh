make setup        # install requirements
make test         # run pytest
make regen-synth  # manually recreate synthetic.nc
make build        # build Docker image
APP_VERSION=$(git rev-parse --short HEAD) make run          # run container


#  Test:
# health and info and metrics
curl "http://localhost:8000/health"
# open in browser https://organic-space-waffle-4rw464p7pp93gq6-8000.app.github.dev/health
curl "http://localhost:8000/info"
# open in browser https://organic-space-waffle-4rw464p7pp93gq6-8000.app.github.dev/info
curl "http://localhost:8000/metrics"
# open in browser https://organic-space-waffle-4rw464p7pp93gq6-8000.app.github.dev/metrics

# JSON: stats
curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/stats?qa=0.75"

# JSON: histogram
curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/histogram?qa=0.75&bins=12"

# PNG: quicklook
curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/quicklook?qa=0.75" -o quicklook.png
file quicklook.png

# PNG: histogram
curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/histogram_png?qa=0.75&bins=12" -o hist.png
file hist.png

# CSV: stats
curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/stats_csv?qa=0.75" -o stats.csv
head -n 2 stats.csv

# Metrics and docs
curl "http://localhost:8000/metrics" | head
# open http://localhost:8000/docs ; https://organic-space-waffle-4rw464p7pp93gq6-8000.app.github.dev/docs
# open http://localhost:8000/redoc ; https://organic-space-waffle-4rw464p7pp93gq6-8000.app.github.dev/redoc
# open https://organic-space-waffle-4rw464p7pp93gq6-8000.app.github.dev/metrics
# OpenAPI JSON: https://organic-space-waffle-4rw464p7pp93gq6-8000.app.github.dev/openapi.json

# Sanity Check
ls -lh quicklook.png
file quicklook.png          # should say: PNG image data
open quicklook.png          # (or click it in the VS Code Explorer)

