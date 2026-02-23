"""
api.py

FastAPI wrapper around the LangGraph image-organizer workflow.
Start with:  uvicorn api:app --app-dir src --host 0.0.0.0 --port 8000 --reload
"""

from pathlib import Path
from typing import Optional

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from image_organization.vision_workflow import run_vision_workflow
from image_organization.workflow import run_workflow
from model_config import VISION_MODEL

app = FastAPI(
    title="Desktop Image Organizer",
    description="Recursively scan a directory for PNG/JPEG images and move them to a destination.",
    version="0.1.0",
)

# Resolve config path relative to this file so it works regardless of working directory.
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.yaml"


def _load_config() -> dict:
    if not _CONFIG_PATH.exists():
        return {}
    with _CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


class DescribeRequest(BaseModel):
    """Describe a single image using the llama3.2-vision model."""
    image_name: Optional[str] = None        # defaults to describe_image_name from config
    search_directory: Optional[str] = None  # defaults to destination_directory from config


class DescribeResponse(BaseModel):
    image_name: str
    search_directory: str
    found: bool
    image_path: Optional[str] = None
    description: Optional[str] = None
    error: Optional[str] = None


class OrganizeRequest(BaseModel):
    """All fields are optional; missing values fall back to config.yaml."""
    source_directory: Optional[str] = None
    destination_directory: Optional[str] = None
    ignored_log: Optional[str] = None
    moved_log: Optional[str] = None
    retain_copy: Optional[bool] = None


class OrganizeResponse(BaseModel):
    source_directory: str
    destination_directory: str
    ignored_log: str
    moved_log: str
    retain_copy: bool
    agent_summary: str


@app.post("/describe", response_model=DescribeResponse)
def describe(request: DescribeRequest):
    """
    Describe a single image using llama3.2-vision.

    *image_name* is the filename to look for (e.g. ``photo.jpg``).
    *search_directory* defaults to ``destination_directory`` from config.yaml.

    Returns a plain-language description of the image, or a clear error if the
    file cannot be found — the vision model is never called for missing files.
    """
    config = _load_config()

    image_name  = request.image_name      or config.get("describe_image_name", "").strip()
    search_dir  = request.search_directory or config.get("destination_directory", "")

    if not image_name:
        raise HTTPException(
            status_code=400,
            detail="image_name is required (set describe_image_name in config.yaml or pass it in the request body).",
        )
    if not search_dir:
        raise HTTPException(
            status_code=400,
            detail="search_directory is required (set destination_directory in config.yaml or pass it in the request body).",
        )

    result = run_vision_workflow(
        image_name=image_name,
        search_directory=search_dir,
        model_name=VISION_MODEL,
    )

    return DescribeResponse(
        image_name=image_name,
        search_directory=search_dir,
        **result,
    )


@app.get("/health")
def health():
    """Simple liveness check."""
    return {"status": "ok"}


@app.post("/organize", response_model=OrganizeResponse)
def organize(request: OrganizeRequest = OrganizeRequest()):
    """
    Trigger the image-organizer workflow.

    Request body fields all override the corresponding config.yaml values.
    If a field is omitted the config.yaml value is used.
    """
    config = _load_config()
    model_cfg = config.get("model", {})

    source_dir  = request.source_directory      or config.get("source_directory", "")
    dest_dir    = request.destination_directory  or config.get("destination_directory", "")
    ignored_log = request.ignored_log            or config.get("ignored_log", "ignored_images.log")
    moved_log   = request.moved_log              or config.get("moved_log", "moved_images.log")
    retain_copy = request.retain_copy if request.retain_copy is not None else bool(config.get("retain_copy", False))
    model_name  = model_cfg.get("name", "llama3.2")
    temperature = float(model_cfg.get("temperature", 0.0))

    if not source_dir:
        raise HTTPException(
            status_code=400,
            detail="source_directory is required (set it in config.yaml or the request body).",
        )
    if not dest_dir:
        raise HTTPException(
            status_code=400,
            detail="destination_directory is required (set it in config.yaml or the request body).",
        )

    summary = run_workflow(
        source_dir=source_dir,
        destination_dir=dest_dir,
        ignored_log=ignored_log,
        moved_log=moved_log,
        retain_copy=retain_copy,
        model_name=model_name,
        temperature=temperature,
    )

    return OrganizeResponse(
        source_directory=source_dir,
        destination_directory=dest_dir,
        ignored_log=ignored_log,
        moved_log=moved_log,
        retain_copy=retain_copy,
        agent_summary=summary,
    )
