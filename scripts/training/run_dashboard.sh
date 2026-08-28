#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

echo "=== TankTrouble AI Train - Dashboard Runner ==="

# 1. Activate Python virtualenv if present
if [ -f ".venv-wsl/bin/activate" ]; then
  source ".venv-wsl/bin/activate"
fi

# 2. Ensure FastAPI and Uvicorn are installed
if ! python -c "import fastapi, uvicorn" >/dev/null 2>&1; then
  echo "Installing FastAPI and Uvicorn..."
  python -m pip install fastapi uvicorn pynvml
fi

# 3. Export Python Path
export PYTHONPATH="build:python:${PYTHONPATH:-}"

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"

echo "Starting Telemetry & Dashboard Server on http://${HOST}:${PORT}"
exec python -m tanktrain.dashboard_server --host "$HOST" --port "$PORT"
