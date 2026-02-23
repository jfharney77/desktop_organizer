#!/usr/bin/env bash
# run_uv.sh
# Start the FastAPI server using the uv-managed .venv environment.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"
echo "Project root: $PROJECT_ROOT"

if [ ! -d ".venv" ]; then
    echo "Error: .venv not found. Run install_uv.sh first."
    exit 1
fi

echo "Starting FastAPI server on http://0.0.0.0:8000 ..."
uv run uvicorn api:app --app-dir src --host 0.0.0.0 --port 8000 --reload
