#!/bin/bash
set -e

echo "Waiting for database to be ready..."
# The depends_on in docker-compose.yml handles the port availability, 
# but it's good practice to let the app naturally retry or just let Alembic run.

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
