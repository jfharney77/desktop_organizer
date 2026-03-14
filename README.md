# Desktop Image Organizer

A desktop image organizer that recursively scans directories for PNG/JPEG images, filters out git-tracked files, and moves or copies them to a centralized destination. Includes an optional vision service to describe images using a local LLM.

---

## Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- [Ollama](https://ollama.com/) — required only for the vision service

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/jfharney/desktop_organizer.git
cd desktop_organizer
```

### 2. Install dependencies

**Using uv (recommended):**
```bash
bash script/bash/install_uv.sh
```

**Using pip:**
```bash
bash script/bash/install_pip.sh
```

This creates a virtual environment (`.venv/` or `.pipvenv/`) and installs all dependencies from `requirements.txt`.

### 3. Configure paths

Edit `config/config.yaml` before running:

```yaml
source_directory: "/path/to/your/images"       # Directory to scan recursively
destination_directory: "/path/to/organized"    # Where images will be moved
ignored_log: "/path/to/ignored_images.log"     # Log of skipped git-tracked images
moved_log: "/path/to/moved_images.log"         # Markdown table log of all moves
retain_copy: false                             # true = copy, false = move
```

---

## Image Organization

### How it works

The organizer runs a two-step [LangGraph](https://github.com/langchain-ai/langgraph) `StateGraph` workflow:

```
scan_node  →  move_node  →  END
```

**Step 1 — Scan**

`scan_node` recursively walks the `source_directory` looking for files with `.png`, `.jpg`, or `.jpeg` extensions. For each image found, it checks whether the file lives inside a git repository (by walking up the directory tree looking for a `.git` folder). Images inside git repos are excluded and written to the `ignored_log`. All other images are collected into a list and passed to the next step via graph state.

**Step 2 — Move**

`move_node` takes the list of image paths produced by the scan and moves (or copies) each file to `destination_directory`. If a filename already exists at the destination, a numeric suffix is appended (`photo_1.jpg`, `photo_2.jpg`, etc.) to avoid overwriting. Every successfully moved file is appended to `moved_log` as a markdown table row.

> **Why LangGraph instead of a plain script?**
> A `StateGraph` passes data between steps through typed state — the LLM never touches the file path list. This avoids a known reliability problem with local models (llama3.2, etc.) where a ReAct agent will drop or truncate large path lists, causing images to never actually be moved.

### Running the organizer

**Option A — Standalone CLI (no server needed)**

Reads directly from `config/config.yaml`:

```bash
python src/image_organization/main.py
```

**Option B — Via the API server + CLI client**

```bash
# Terminal 1: start the server
bash script/bash/run_uv.sh

# Terminal 2: trigger a run (uses config.yaml values by default)
python src/clients/client.py

# Or override paths at runtime:
python src/clients/client.py --source /path/to/source --dest /path/to/dest
```

The server exposes `POST /organize` on port 8000. Request body fields override `config.yaml` values — omitted fields fall back to the config.

### Output logs

| Log | Format | Purpose |
|-----|--------|---------|
| `ignored_log` | Plain text, one path per line | Images skipped because they live inside a git repo |
| `moved_log` | Markdown table | Record of every move: original path, new path, timestamp, whether a copy was retained |

---

## Vision Service (optional)

Describes images using `llama3.2-vision` via Ollama. See `script/bash/install_vision_uv.sh` and `script/bash/run_vision_uv.sh` to set up and run the vision service on port 8001.

---

## Project Structure

```
src/
  api.py                          # FastAPI entry point (ports 8000 / 8001)
  model_config.py                 # Ollama model factory functions
  image_organization/
    workflow.py                   # LangGraph StateGraph for organizing
    tools.py                      # Scan and move implementations
    vision_workflow.py            # LangGraph StateGraph for vision
    vision_tools.py               # Vision model tools
    main.py                       # Standalone CLI entry point
  clients/
    client.py                     # CLI client for /organize
    vision_client.py              # CLI client for /describe
config/
  config.yaml                     # Runtime configuration
script/
  bash/                           # Linux/macOS shell scripts
  bat/                            # Windows batch scripts
```
