#!/usr/bin/env bash
# run_pip.sh
# Start the FastAPI server using the pip-managed .pipvenv environment.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$PROJECT_ROOT"
echo "Project root: $PROJECT_ROOT"

if [ ! -d ".pipvenv" ]; then
    echo "Error: .pipvenv not found. Run install_pip.sh first."
    exit 1
fi

echo "Starting FastAPI server on http://0.0.0.0:8000 ..."
source .pipvenv/bin/activate
uvicorn api:app --app-dir src --host 0.0.0.0 --port 8000 --reload
