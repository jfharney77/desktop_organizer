#!/usr/bin/env bash
# install_uv.sh
# Create a uv-managed virtual environment (.venv) and install all dependencies.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"
echo "Project root: $PROJECT_ROOT"

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "uv not found — installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Make uv available in the current session
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

echo "uv version: $(uv --version)"

echo "Creating virtual environment in .venv ..."
uv venv .venv

echo "Installing dependencies from requirements.txt ..."
uv pip install --link-mode=copy -r requirements.txt

echo ""
echo "Done!  To activate manually: source .venv/bin/activate"
