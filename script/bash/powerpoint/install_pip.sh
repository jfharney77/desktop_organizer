#!/usr/bin/env bash
# install_pip.sh  (powerpoint)
# Create a pip-managed virtual environment (.pipvenv) and install all dependencies.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$PROJECT_ROOT"
echo "Project root: $PROJECT_ROOT"

echo "Creating virtual environment in .pipvenv ..."
python3 -m venv .pipvenv

echo "Upgrading pip ..."
.pipvenv/bin/pip install --upgrade pip

echo "Installing dependencies from requirements.txt ..."
.pipvenv/bin/pip install -r requirements.txt

echo ""
echo "Done!  To activate manually: source .pipvenv/bin/activate"
