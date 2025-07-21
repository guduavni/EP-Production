#!/bin/bash

# Exit on error
set -e

# Set environment variables
export FLASK_APP=run_simple.py
export FLASK_ENV=production
export PYTHONUNBUFFERED=1

# Create required directories
mkdir -p logs

# Install dependencies if needed
pip install -r requirements.txt

# Run database migrations (if any)
python init_db.py

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 120 --log-file=./logs/gunicorn.log --access-logfile=./logs/access.log run_simple:app

# For development with auto-reload, use:
# gunicorn --bind 0.0.0.0:8000 --reload --log-level=debug --error-logfile=./logs/error.log run_simple:app
