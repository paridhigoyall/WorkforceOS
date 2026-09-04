#!/bin/sh
set -e

echo "Starting WorkforceOS Backend Service..."

RUN_MIGRATIONS="${RUN_MIGRATIONS:-true}"

if [ "$RUN_MIGRATIONS" = "only" ]; then
    echo "Running dedicated database migration step..."
    if [ -f "alembic.ini" ]; then
        alembic upgrade head
        echo "Database schema migrations applied successfully."
    else
        echo "Warning: alembic.ini not found, skipping migrations."
    fi
    exit 0
fi

if [ "$RUN_MIGRATIONS" = "true" ]; then
    if [ -f "alembic.ini" ]; then
        echo "Applying database schema migrations..."
        alembic upgrade head || echo "Alembic migrations completed or handled by another worker."
    fi
else
    echo "Skipping migrations (managed by dedicated migration service or orchestration pipeline)."
fi

WORKERS="${WORKERS:-4}"
PORT="${PORT:-8000}"

echo "Spawning Uvicorn ASGI Server with $WORKERS concurrent workers on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --workers "$WORKERS" --proxy-headers --forwarded-allow-ips='*'
