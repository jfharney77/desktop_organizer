#!/usr/bin/env bash
# install_vision_pip.sh
# Install Python dependencies (pip) and pull the llama3.2-vision Ollama model.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$PROJECT_ROOT"
echo "Project root: $PROJECT_ROOT"

# --- Python dependencies ---
if [ ! -d ".pipvenv" ]; then
    echo "Creating virtual environment in .pipvenv ..."
    python3 -m venv .pipvenv

    echo "Upgrading pip ..."
    .pipvenv/bin/pip install --upgrade pip

    echo "Installing dependencies from requirements.txt ..."
    .pipvenv/bin/pip install -r requirements.txt
else
    echo ".pipvenv already exists — skipping Python install."
fi

# --- Ollama model ---
if ! command -v ollama &> /dev/null; then
    echo ""
    echo "Error: ollama is not installed or not on PATH."
    echo "Install it from https://ollama.com and re-run this script."
    exit 1
fi

echo ""
echo "Pulling llama3.2-vision model (this may take a while on first run) ..."
ollama pull llama3.2-vision

echo ""
echo "Done!  Run the vision service with: bash script/bash/run_vision_pip.sh"
