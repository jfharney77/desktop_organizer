#!/usr/bin/env bash
# install_vision_uv.sh
# Install Python dependencies (uv) and pull the llama3.2-vision Ollama model.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"
echo "Project root: $PROJECT_ROOT"

# --- uv ---
if ! command -v uv &> /dev/null; then
    echo "uv not found — installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

echo "uv version: $(uv --version)"

# --- Python dependencies ---
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment in .venv ..."
    uv venv .venv

    echo "Installing dependencies from requirements.txt ..."
    uv pip install --link-mode=copy -r requirements.txt
else
    echo ".venv already exists — skipping Python install."
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
echo "Done!  Run the vision service with: bash script/bash/run_vision_uv.sh"
