#!/usr/bin/env bash
# run_frontend.sh
# Start the React dev server on http://localhost:3000

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "Error: node_modules not found. Run 'npm install' in the frontend/ directory first."
    exit 1
fi

echo "Starting React dev server on http://localhost:3000 ..."
cd "$FRONTEND_DIR"
npm run dev
