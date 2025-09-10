make setup        # install requirements
make test         # run pytest
make regen-synth  # manually recreate synthetic.nc
make build        # build Docker image
make run          # run container


#  Test:
curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/stats?qa=0.75"
curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/histogram?qa=0.75&bins=12"
curl -F "file=@tests/data/synthetic.nc" "http://localhost:8000/quicklook?qa=0.75" -o quicklook.png

# Sanity Check
ls -lh quicklook.png
file quicklook.png          # should say: PNG image data
open quicklook.png          # (or click it in the VS Code Explorer)

