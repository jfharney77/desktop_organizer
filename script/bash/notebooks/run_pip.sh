#!/usr/bin/env bash
# run_pip.sh  (notebooks)
# Launch Jupyter Notebook from the project root using the pip-managed .pipvenv environment.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$PROJECT_ROOT"
echo "Project root: $PROJECT_ROOT"

if [ ! -d ".pipvenv" ]; then
    echo "Error: .pipvenv not found. Run script/bash/image/install_pip.sh first."
    exit 1
fi

echo "Starting Jupyter Notebook (notebooks/ directory) ..."
echo ""
source .pipvenv/bin/activate
jupyter notebook --notebook-dir=notebooks
