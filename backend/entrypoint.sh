#!/bin/sh
set -e

echo "Starting WorkforceOS Backend Service..."

# Run database migrations if alembic config is present
if [ -f "alembic.ini" ]; then
    echo "Applying database schema migrations..."
    alembic upgrade head || echo "Alembic migrations skipped or handled automatically."
fi

WORKERS="${WORKERS:-4}"
PORT="${PORT:-8000}"

echo "Spawning Uvicorn ASGI Server with $WORKERS concurrent workers on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --workers "$WORKERS" --proxy-headers --forwarded-allow-ips='*'
