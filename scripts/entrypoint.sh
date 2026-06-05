#!/bin/sh
set -e

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000