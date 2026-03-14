"""
api.py

FastAPI wrapper around the LangGraph image-organizer workflow.
Start with:  uvicorn api:app --app-dir src --host 0.0.0.0 --port 8000 --reload
"""

import json
from pathlib import Path
from typing import List, Optional

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from image_vision.vision_workflow import run_vision_workflow
from image_organization.tools import _scan_images_impl, IMAGE_EXTENSIONS, _is_in_git_repo as _img_in_git
from image_organization.workflow import run_workflow
from powerpoint_organization.tools import _scan_pptx_impl, PPTX_EXTENSIONS, _is_in_git_repo as _pptx_in_git
from powerpoint_organization.workflow import run_workflow as run_pptx_workflow
from txt_organization.tools import _scan_txt_impl, TXT_EXTENSIONS, _is_in_git_repo as _txt_in_git
from txt_organization.workflow import run_workflow as run_txt_workflow
from git_organization.tools import is_git_repo, _scan_git_repos_impl
from git_organization.workflow import run_workflow as run_git_workflow
from model_config import VISION_MODEL
from stream_utils import stream_move_files, stream_move_dirs

app = FastAPI(
    title="Desktop Image Organizer",
    description="Recursively scan a directory for PNG/JPEG images and move them to a destination.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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
    extensions: Optional[List[str]] = None
    file_paths: Optional[List[str]] = None  # if set, skip scan and move only these files


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

    vision_cfg  = config.get("vision", {})
    image_name  = request.image_name      or vision_cfg.get("describe_image_name", "").strip()
    search_dir  = request.search_directory or vision_cfg.get("search_directory", "").strip() or config.get("images", {}).get("destination_directory", "")

    if not image_name:
        raise HTTPException(
            status_code=400,
            detail="image_name is required (set vision.describe_image_name in config.yaml or pass it in the request body).",
        )
    if not search_dir:
        raise HTTPException(
            status_code=400,
            detail="search_directory is required (set vision.search_directory in config.yaml or pass it in the request body).",
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
    config    = _load_config()
    img_cfg   = config.get("images", {})
    model_cfg = config.get("model", {})

    source_dir  = request.source_directory      or img_cfg.get("source_directory", "")
    dest_dir    = request.destination_directory  or img_cfg.get("destination_directory", "")
    ignored_log = request.ignored_log            or img_cfg.get("ignored_log", "ignored_images.log")
    moved_log   = request.moved_log              or img_cfg.get("moved_log", "moved_images.log")
    retain_copy = request.retain_copy if request.retain_copy is not None else bool(img_cfg.get("retain_copy", False))
    extensions  = request.extensions if request.extensions is not None else img_cfg.get("extensions", [".png", ".jpg", ".jpeg"])
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
        extensions=extensions,
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


class PptxOrganizeRequest(BaseModel):
    """All fields are optional; missing values fall back to config.yaml powerpoint section."""
    source_directory: Optional[str] = None
    destination_directory: Optional[str] = None
    ignored_log: Optional[str] = None
    moved_log: Optional[str] = None
    retain_copy: Optional[bool] = None
    file_paths: Optional[List[str]] = None  # if set, skip scan and move only these files


@app.post("/organize/pptx", response_model=OrganizeResponse)
def organize_pptx(request: PptxOrganizeRequest = PptxOrganizeRequest()):
    """
    Trigger the PowerPoint organizer workflow.

    Recursively scans source_directory for .pptx and .ppt files and moves
    them to destination_directory. Request body fields override config.yaml
    powerpoint section values.
    """
    config = _load_config()
    pptx_cfg = config.get("powerpoint", {})

    source_dir  = request.source_directory      or pptx_cfg.get("source_directory", "")
    dest_dir    = request.destination_directory  or pptx_cfg.get("destination_directory", "")
    ignored_log = request.ignored_log            or pptx_cfg.get("ignored_log", "ignored_pptx.log")
    moved_log   = request.moved_log              or pptx_cfg.get("moved_log", "moved_pptx.log")
    retain_copy = request.retain_copy if request.retain_copy is not None else bool(pptx_cfg.get("retain_copy", False))

    if not source_dir:
        raise HTTPException(
            status_code=400,
            detail="source_directory is required (set it in config.yaml under 'powerpoint' or pass it in the request body).",
        )
    if not dest_dir:
        raise HTTPException(
            status_code=400,
            detail="destination_directory is required (set it in config.yaml under 'powerpoint' or pass it in the request body).",
        )

    summary = run_pptx_workflow(
        source_dir=source_dir,
        destination_dir=dest_dir,
        ignored_log=ignored_log,
        moved_log=moved_log,
        retain_copy=retain_copy,
    )

    return OrganizeResponse(
        source_directory=source_dir,
        destination_directory=dest_dir,
        ignored_log=ignored_log,
        moved_log=moved_log,
        retain_copy=retain_copy,
        agent_summary=summary,
    )


class TxtOrganizeRequest(BaseModel):
    """All fields are optional; missing values fall back to config.yaml txt section."""
    source_directory: Optional[str] = None
    destination_directory: Optional[str] = None
    ignored_log: Optional[str] = None
    moved_log: Optional[str] = None
    retain_copy: Optional[bool] = None
    file_paths: Optional[List[str]] = None  # if set, skip scan and move only these files


@app.post("/organize/txt", response_model=OrganizeResponse)
def organize_txt(request: TxtOrganizeRequest = TxtOrganizeRequest()):
    """
    Trigger the text file organizer workflow.

    Recursively scans source_directory for .txt files and moves them to
    destination_directory. Request body fields override config.yaml txt
    section values.
    """
    config  = _load_config()
    txt_cfg = config.get("txt", {})

    source_dir  = request.source_directory      or txt_cfg.get("source_directory", "")
    dest_dir    = request.destination_directory  or txt_cfg.get("destination_directory", "")
    ignored_log = request.ignored_log            or txt_cfg.get("ignored_log", "ignored_txt.log")
    moved_log   = request.moved_log              or txt_cfg.get("moved_log", "moved_txt.log")
    retain_copy = request.retain_copy if request.retain_copy is not None else bool(txt_cfg.get("retain_copy", False))

    if not source_dir:
        raise HTTPException(
            status_code=400,
            detail="source_directory is required (set it in config.yaml under 'txt' or pass it in the request body).",
        )
    if not dest_dir:
        raise HTTPException(
            status_code=400,
            detail="destination_directory is required (set it in config.yaml under 'txt' or pass it in the request body).",
        )

    summary = run_txt_workflow(
        source_dir=source_dir,
        destination_dir=dest_dir,
        ignored_log=ignored_log,
        moved_log=moved_log,
        retain_copy=retain_copy,
    )

    return OrganizeResponse(
        source_directory=source_dir,
        destination_directory=dest_dir,
        ignored_log=ignored_log,
        moved_log=moved_log,
        retain_copy=retain_copy,
        agent_summary=summary,
    )


# ---------------------------------------------------------------------------
# Git repository check
# ---------------------------------------------------------------------------

class GitRepoCheckResponse(BaseModel):
    path: str
    exists: bool
    is_git_repo: bool
    repo_count: int
    repos: List[str]


@app.get("/check/git-repo", response_model=GitRepoCheckResponse)
def check_git_repo(path: str):
    """
    Check whether *path* is itself a git repository and return all git
    repositories found as subdirectories.
    """
    p = Path(path)
    if not p.exists() or not p.is_dir():
        return GitRepoCheckResponse(path=path, exists=False, is_git_repo=False, repo_count=0, repos=[])

    result = _scan_git_repos_impl(path, ignored_log="")
    repos  = result.get("found", [])
    return GitRepoCheckResponse(
        path=path,
        exists=True,
        is_git_repo=is_git_repo(p),
        repo_count=len(repos),
        repos=repos,
    )


# ---------------------------------------------------------------------------
# File-type check endpoints (scan without writing logs)
# ---------------------------------------------------------------------------

class FileCheckResponse(BaseModel):
    path: str
    exists: bool
    file_count: int
    files: List[str]


def _quick_scan(path: str, extensions: set, git_filter) -> FileCheckResponse:
    p = Path(path)
    if not p.exists() or not p.is_dir():
        return FileCheckResponse(path=path, exists=False, file_count=0, files=[])
    files = [
        str(f) for f in p.rglob("*")
        if f.is_file() and f.suffix.lower() in extensions and not git_filter(f)
    ]
    return FileCheckResponse(path=path, exists=True, file_count=len(files), files=files)


@app.get("/check/images", response_model=FileCheckResponse)
def check_images(path: str):
    """Return all image files found in *path* (git-tracked files excluded)."""
    return _quick_scan(path, IMAGE_EXTENSIONS, _img_in_git)


@app.get("/check/pptx", response_model=FileCheckResponse)
def check_pptx(path: str):
    """Return all .pptx/.ppt files found in *path* (git-tracked files excluded)."""
    return _quick_scan(path, PPTX_EXTENSIONS, _pptx_in_git)


@app.get("/check/txt", response_model=FileCheckResponse)
def check_txt(path: str):
    """Return all .txt files found in *path* (git-tracked files excluded)."""
    return _quick_scan(path, TXT_EXTENSIONS, _txt_in_git)


# ---------------------------------------------------------------------------
# Git repository organizer
# ---------------------------------------------------------------------------

class GitOrganizeRequest(BaseModel):
    """All fields are optional; missing values fall back to config.yaml git section."""
    source_directory: Optional[str] = None
    destination_directory: Optional[str] = None
    ignored_log: Optional[str] = None
    moved_log: Optional[str] = None
    retain_copy: Optional[bool] = None
    repo_paths: Optional[List[str]] = None  # if set, skip scan and move only these repos


@app.post("/organize/git", response_model=OrganizeResponse)
def organize_git(request: GitOrganizeRequest = GitOrganizeRequest()):
    """
    Trigger the git repository organizer workflow.

    Recursively scans source_directory for directories containing a .git
    folder and moves them to destination_directory. Request body fields
    override config.yaml git section values.
    """
    config  = _load_config()
    git_cfg = config.get("git", {})

    source_dir  = request.source_directory      or git_cfg.get("source_directory", "")
    dest_dir    = request.destination_directory  or git_cfg.get("destination_directory", "")
    ignored_log = request.ignored_log            or git_cfg.get("ignored_log", "ignored_git.log")
    moved_log   = request.moved_log              or git_cfg.get("moved_log", "moved_git.log")
    retain_copy = request.retain_copy if request.retain_copy is not None else bool(git_cfg.get("retain_copy", False))

    if not source_dir:
        raise HTTPException(
            status_code=400,
            detail="source_directory is required (set it in config.yaml under 'git' or pass it in the request body).",
        )
    if not dest_dir:
        raise HTTPException(
            status_code=400,
            detail="destination_directory is required (set it in config.yaml under 'git' or pass it in the request body).",
        )

    summary = run_git_workflow(
        source_dir=source_dir,
        destination_dir=dest_dir,
        ignored_log=ignored_log,
        moved_log=moved_log,
        retain_copy=retain_copy,
        repo_paths=request.repo_paths or [],
    )

    return OrganizeResponse(
        source_directory=source_dir,
        destination_directory=dest_dir,
        ignored_log=ignored_log,
        moved_log=moved_log,
        retain_copy=retain_copy,
        agent_summary=summary,
    )


# ---------------------------------------------------------------------------
# SSE streaming endpoints
# ---------------------------------------------------------------------------

def _sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


@app.post("/organize/stream")
async def organize_stream(request: OrganizeRequest = OrganizeRequest()):
    config    = _load_config()
    img_cfg   = config.get("images", {})

    source_dir  = request.source_directory      or img_cfg.get("source_directory", "")
    dest_dir    = request.destination_directory  or img_cfg.get("destination_directory", "")
    ignored_log = request.ignored_log            or img_cfg.get("ignored_log", "ignored_images.log")
    moved_log   = request.moved_log              or img_cfg.get("moved_log", "moved_images.log")
    retain_copy = request.retain_copy if request.retain_copy is not None else bool(img_cfg.get("retain_copy", False))
    extensions  = request.extensions if request.extensions is not None else img_cfg.get("extensions", [".png", ".jpg", ".jpeg"])

    if not source_dir or not dest_dir:
        raise HTTPException(status_code=400, detail="source_directory and destination_directory are required.")

    async def generate():
        if request.file_paths:
            found = list(request.file_paths)
        else:
            yield _sse({"type": "scanning"})
            scan = _scan_images_impl(source_dir, ignored_log, set(extensions))
            found = scan.get("found", [])
        yield _sse({"type": "scan_complete", "total": len(found)})
        async for event in stream_move_files(found, dest_dir, moved_log, retain_copy):
            yield _sse(event)

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/organize/pptx/stream")
async def organize_pptx_stream(request: PptxOrganizeRequest = PptxOrganizeRequest()):
    config   = _load_config()
    pptx_cfg = config.get("powerpoint", {})

    source_dir  = request.source_directory      or pptx_cfg.get("source_directory", "")
    dest_dir    = request.destination_directory  or pptx_cfg.get("destination_directory", "")
    ignored_log = request.ignored_log            or pptx_cfg.get("ignored_log", "ignored_pptx.log")
    moved_log   = request.moved_log              or pptx_cfg.get("moved_log", "moved_pptx.log")
    retain_copy = request.retain_copy if request.retain_copy is not None else bool(pptx_cfg.get("retain_copy", False))

    if not source_dir or not dest_dir:
        raise HTTPException(status_code=400, detail="source_directory and destination_directory are required.")

    async def generate():
        if request.file_paths:
            found = list(request.file_paths)
        else:
            yield _sse({"type": "scanning"})
            scan = _scan_pptx_impl(source_dir, ignored_log)
            found = scan.get("found", [])
        yield _sse({"type": "scan_complete", "total": len(found)})
        async for event in stream_move_files(found, dest_dir, moved_log, retain_copy):
            yield _sse(event)

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/organize/txt/stream")
async def organize_txt_stream(request: TxtOrganizeRequest = TxtOrganizeRequest()):
    config  = _load_config()
    txt_cfg = config.get("txt", {})

    source_dir  = request.source_directory      or txt_cfg.get("source_directory", "")
    dest_dir    = request.destination_directory  or txt_cfg.get("destination_directory", "")
    ignored_log = request.ignored_log            or txt_cfg.get("ignored_log", "ignored_txt.log")
    moved_log   = request.moved_log              or txt_cfg.get("moved_log", "moved_txt.log")
    retain_copy = request.retain_copy if request.retain_copy is not None else bool(txt_cfg.get("retain_copy", False))

    if not source_dir or not dest_dir:
        raise HTTPException(status_code=400, detail="source_directory and destination_directory are required.")

    async def generate():
        if request.file_paths:
            found = list(request.file_paths)
        else:
            yield _sse({"type": "scanning"})
            scan = _scan_txt_impl(source_dir, ignored_log)
            found = scan.get("found", [])
        yield _sse({"type": "scan_complete", "total": len(found)})
        async for event in stream_move_files(found, dest_dir, moved_log, retain_copy):
            yield _sse(event)

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/organize/git/stream")
async def organize_git_stream(request: GitOrganizeRequest = GitOrganizeRequest()):
    config  = _load_config()
    git_cfg = config.get("git", {})

    source_dir  = request.source_directory      or git_cfg.get("source_directory", "")
    dest_dir    = request.destination_directory  or git_cfg.get("destination_directory", "")
    ignored_log = request.ignored_log            or git_cfg.get("ignored_log", "ignored_git.log")
    moved_log   = request.moved_log              or git_cfg.get("moved_log", "moved_git.log")
    retain_copy = request.retain_copy if request.retain_copy is not None else bool(git_cfg.get("retain_copy", False))

    if not source_dir or not dest_dir:
        raise HTTPException(status_code=400, detail="source_directory and destination_directory are required.")

    async def generate():
        if request.repo_paths:
            found = list(request.repo_paths)
        else:
            yield _sse({"type": "scanning"})
            scan = _scan_git_repos_impl(source_dir, ignored_log)
            found = scan.get("found", [])
        yield _sse({"type": "scan_complete", "total": len(found)})
        async for event in stream_move_dirs(found, dest_dir, moved_log, retain_copy):
            yield _sse(event)

    return StreamingResponse(generate(), media_type="text/event-stream")
