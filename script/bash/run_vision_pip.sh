#!/usr/bin/env bash
# run_vision_pip.sh
# Start the vision FastAPI service on port 8001 using the pip-managed .pipvenv environment.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"
echo "Project root: $PROJECT_ROOT"

if [ ! -d ".pipvenv" ]; then
    echo "Error: .pipvenv not found. Run install_vision_pip.sh first."
    exit 1
fi

echo "Starting vision FastAPI service on http://0.0.0.0:8001 ..."
echo "Endpoint: POST http://localhost:8001/describe"
echo ""
source .pipvenv/bin/activate
uvicorn api:app --app-dir src --host 0.0.0.0 --port 8001 --reload
