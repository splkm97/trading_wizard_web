#!/bin/sh
set -e

echo "Running migrations..."
alembic upgrade head

echo "Seeding historical prices data..."
python scripts/seed_historical_prices.py

echo "Starting server..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
