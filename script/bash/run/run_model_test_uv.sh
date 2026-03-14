#!/usr/bin/env bash
# run_model_test_uv.sh
# Run the model_config.py tester using the uv-managed .venv environment.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$PROJECT_ROOT"
echo "Project root: $PROJECT_ROOT"

if [ ! -d ".venv" ]; then
    echo "Error: .venv not found. Run install_uv.sh first."
    exit 1
fi

echo "Running model_config.py tester ..."
echo ""
uv run python src/model_config.py
