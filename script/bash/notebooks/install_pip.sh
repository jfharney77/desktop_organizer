#!/usr/bin/env bash
# install_pip.sh  (notebooks)
# Install Jupyter into the pip-managed .pipvenv environment.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$PROJECT_ROOT"
echo "Project root: $PROJECT_ROOT"

if [ ! -d ".pipvenv" ]; then
    echo "Error: .pipvenv not found. Run script/bash/image/install_pip.sh first."
    exit 1
fi

echo "Installing Jupyter into .pipvenv ..."
.pipvenv/bin/pip install notebook

echo ""
echo "Done!  Launch notebooks with: bash script/bash/notebooks/run_pip.sh"
