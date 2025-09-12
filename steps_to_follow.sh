# /workspaces/rb-tropomi-no2-quicklook/steps_to_follow.sh
# This file contains a list of steps done for this project
# and the scripts. It is not meant to be executed.

# Project Kickoff
# “TROPOMI NO₂ Quicklook & QA Microservice” (Sentinel-5P)

# What it does

# 1. Ingests a Sentinel-5P TROPOMI NO₂ product (NetCDF/HDF5 is typical).

# 2. Applies a QA filter (e.g., qa_value >= 0.75) to keep only reliable pixels.

# Produces:

#       1. /stats → JSON with min/mean/max/count of valid NO₂

#       2. /quicklook → PNG quicklook of filtered NO₂ field

# 3. Ships as a containerized FastAPI microservice with tests + CI.

# 4. Uses a tiny synthetic NetCDF for deterministic testing (no big downloads).

# 5. Designed to extend with Airflow / Dask / Swarm / K8s / Grafana later.



# Step 1: Set up the project structure and environment
# mkdir rb-tropomi-no2-quicklook
# cd rb-tropomi-no2-quicklook
# python3 -m venv venv
# source venv/bin/activate

# Step 2: Install necessary libraries in requirements.txt

# Step 3: Create the core modules 
# tropomi/io.py
# tropomi/qa.py
# tropomi/no2.py
# tropomi/render.py

# Step 4: Create the FastAPI app in app/
# app/api.py

# Step 5: Write tests in tests/






# 
