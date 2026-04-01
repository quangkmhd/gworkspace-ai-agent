#!/usr/bin/env bash
# Dev startup script — starts the server with auto-reload
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "🚀 Starting GWorkspace AI Agent (dev mode)..."
echo "   Swagger UI: http://localhost:8000/docs"
echo "   Health:     http://localhost:8000/v1/system/health"
echo ""

exec python -m uvicorn backend.main:app \
    --reload \
    --host "${HOST:-0.0.0.0}" \
    --port "${PORT:-8000}" \
    --log-level "${LOG_LEVEL:-info}"
