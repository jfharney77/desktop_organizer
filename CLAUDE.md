# CLAUDE.md

## Project Overview

A desktop image organizer that recursively scans directories for PNG/JPEG images, filters out git-tracked files, and moves/copies them to a centralized destination. Includes a vision model service to describe images using a local LLM.

## Architecture

### Core Components

- **`src/api.py`** — FastAPI entry point. Port 8000 = `/organize`, port 8001 = `/describe`. Both expose `/health`.
- **`src/image_organization/`** — LangGraph StateGraph workflows for organizing images (scan → move) and vision description (check → describe).
- **`src/clients/`** — CLI clients that POST to the FastAPI endpoints.
- **`src/model_config.py`** — Factory functions for text (`llama3.2`) and vision (`llama3.2-vision`) Ollama models.
- **`config/config.yaml`** — Runtime configuration (source/dest paths, log paths, model settings).

### Key Design Pattern

LangGraph StateGraphs are used deliberately to prevent LLM hallucination — file existence is checked in pure Python before calling the vision model, and state is passed through typed graph state rather than relying on model output.

## External Dependency: Ollama

Ollama must be installed and running before the server starts. Required models:
- `llama3.2` (text)
- `llama3.2-vision` (vision)

The install scripts pull these models automatically.

## Commands

### Install

```bash
# Using uv (recommended)
bash script/bash/install_uv.sh

# Using pip
bash script/bash/install_pip.sh

# Vision service install (also pulls Ollama vision model)
bash script/bash/install_vision_uv.sh
```

### Run

```bash
# Main organizer service (port 8000)
bash script/bash/run_uv.sh
# or manually:
uv run uvicorn api:app --app-dir src --host 0.0.0.0 --port 8000 --reload

# Vision service (port 8001)
bash script/bash/run_vision_uv.sh

# Standalone CLI (no server needed)
python src/image_organization/main.py

# CLI clients
python src/clients/client.py --source /path/to/source --dest /path/to/dest
python src/clients/vision_client.py --image photo.jpg --dir /path/to/images
```

### Test Model Connectivity

```bash
bash script/bash/run_model_test_uv.sh
# Runs src/model_config.py which tests both text and vision model responses
```

## Key Dependencies (`requirements.txt`)

- `langgraph` — StateGraph workflows
- `langchain-ollama` — Local LLM integration
- `fastapi` + `uvicorn` — Web API layer
- `pyyaml` — Config file parsing
- `requests` — HTTP client for CLI clients

## Configuration (`config/config.yaml`)

```yaml
source_directory: "..."        # Root dir to scan for images
destination_directory: "..."   # Where organized images go
ignored_log: "..."             # Log of git-tracked images skipped
moved_log: "..."               # Markdown table log of moved images
retain_copy: true              # true = copy, false = move
model:
  name: "llama3.2"
  temperature: 0.0
```

Config values are defaults; request body fields override them per API call.

## Virtual Environments

- `uv` installs to `.venv/`
- `pip` installs to `.pipvenv/`

Both are gitignored. Windows equivalents use `.bat` scripts in `script/bat/`.

## Git Workflow

- **`main`** — stable production branch
- **`devel`** — active development branch
- Feature branches cut from `main`, e.g. `devel-powerpoint-org`
- PRs target `main`

## No Linting or Test Framework Configured

There is currently no Black, Flake8, pytest, or similar tooling. Model connectivity can be verified with `run_model_test_uv.sh`.
