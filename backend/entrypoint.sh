#!/bin/sh
set -e
if [ ! -f /app/.venv/bin/uvicorn ]; then
  uv sync --frozen --all-groups
fi
exec uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir /app/src
