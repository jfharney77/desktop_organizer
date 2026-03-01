#!/usr/bin/env bash
# install_uv.sh  (notebooks)
# Install Jupyter into the uv-managed .venv environment.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$PROJECT_ROOT"
echo "Project root: $PROJECT_ROOT"

if [ ! -d ".venv" ]; then
    echo "Error: .venv not found. Run script/bash/image/install_uv.sh first."
    exit 1
fi

echo "Installing Jupyter into .venv ..."
uv pip install --link-mode=copy notebook

echo ""
echo "Done!  Launch notebooks with: bash script/bash/notebooks/run_uv.sh"
