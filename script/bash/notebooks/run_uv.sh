#!/usr/bin/env bash
# run_uv.sh  (notebooks)
# Launch Jupyter Notebook from the project root using the uv-managed .venv environment.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$PROJECT_ROOT"
echo "Project root: $PROJECT_ROOT"

if [ ! -d ".venv" ]; then
    echo "Error: .venv not found. Run script/bash/image/install_uv.sh first."
    exit 1
fi

echo "Starting Jupyter Notebook (notebooks/ directory) ..."
echo ""
uv run jupyter notebook --notebook-dir=notebooks
