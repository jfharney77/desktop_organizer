#!/usr/bin/env bash
# run_model_test_pip.sh
# Run the model_config.py tester using the pip-managed .pipvenv environment.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"
echo "Project root: $PROJECT_ROOT"

if [ ! -d ".pipvenv" ]; then
    echo "Error: .pipvenv not found. Run install_pip.sh first."
    exit 1
fi

echo "Running model_config.py tester ..."
echo ""
source .pipvenv/bin/activate
python src/model_config.py
