"""
tools.py

LangChain tools for the PowerPoint organizer, plus the underlying
implementation functions used directly by the StateGraph nodes.

Separating _impl from @tool means the workflow nodes can call the logic
without going through the LLM, avoiding the reliability problem of asking
a local model to pass large file-path lists between tool calls.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool


PPTX_EXTENSIONS = {".pptx", ".ppt", ".pptm"}


def _is_in_git_repo(path: Path) -> bool:
    """Walk up the directory tree; return True if any ancestor contains a .git folder."""
    current = path.resolve().parent
    while True:
        if (current / ".git").exists():
            return True
        parent = current.parent
        if parent == current:  # reached filesystem root
            break
        current = parent
    return False


# ---------------------------------------------------------------------------
# Pure-Python implementations (called directly by StateGraph nodes)
# ---------------------------------------------------------------------------

def _scan_pptx_impl(directory: str, ignored_log: str) -> dict:
    """
    Recursively scan *directory* for PowerPoint files (.pptx, .ppt, .pptm).
    Files inside git repositories are excluded and written to *ignored_log*.
    """
    source = Path(directory)

    if not source.exists():
        return {"error": f"Directory does not exist: {directory}", "found": [], "ignored": []}
    if not source.is_dir():
        return {"error": f"Not a directory: {directory}", "found": [], "ignored": []}

    found: list[str] = []
    ignored: list[str] = []

    for file in source.rglob("*"):
        if file.is_file() and file.suffix.lower() in PPTX_EXTENSIONS:
            if _is_in_git_repo(file):
                ignored.append(str(file))
            else:
                found.append(str(file))

    if ignored:
        log_path = Path(ignored_log)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w", encoding="utf-8") as fh:
            fh.write("\n".join(ignored) + "\n")

    return {
        "found": found,
        "ignored": ignored,
        "summary": (
            f"Found {len(found)} PowerPoint file(s) to move, "
            f"ignored {len(ignored)} file(s) inside git repos "
            f"(logged to {ignored_log})"
        ),
    }


def _move_pptx_impl(
    pptx_paths: list[str],
    destination_directory: str,
    moved_log: str = "",
    retain_copy: bool = False,
) -> dict:
    """
    Move (or copy, if *retain_copy* is True) each file in *pptx_paths* to
    *destination_directory*.  Numeric suffixes (_1, _2, …) are added on name
    conflicts.  A markdown-table log of every moved file is written to
    *moved_log* (appended if the file already exists).
    """
    dest = Path(destination_directory)
    dest.mkdir(parents=True, exist_ok=True)

    moved: list[str] = []
    errors: list[str] = []
    log_rows: list[tuple[str, str, str, str, str]] = []  # (name, orig, new, date, copy)

    for src_str in pptx_paths:
        src = Path(src_str)

        if not src.exists():
            errors.append(f"File not found: {src_str}")
            continue

        dest_file = dest / src.name

        if dest_file.exists():
            counter = 1
            while dest_file.exists():
                dest_file = dest / f"{src.stem}_{counter}{src.suffix}"
                counter += 1

        try:
            if retain_copy:
                shutil.copy2(str(src), str(dest_file))
            else:
                shutil.move(str(src), str(dest_file))
            moved.append(f"{src_str} -> {dest_file}")
            log_rows.append((
                src.name,
                str(src),
                str(dest_file),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Yes" if retain_copy else "No",
            ))
        except Exception as exc:
            errors.append(f"Could not move {src_str}: {exc}")

    if log_rows and moved_log:
        log_path = Path(moved_log)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not log_path.exists() or log_path.stat().st_size == 0
        with log_path.open("a", encoding="utf-8") as fh:
            if write_header:
                fh.write("| Name | Original Location | New Location | Date of Move | Copy Retained |\n")
                fh.write("|------|-------------------|--------------|--------------|---------------|\n")
            for name, orig, new, date, copy in log_rows:
                fh.write(f"| {name} | {orig} | {new} | {date} | {copy} |\n")

    return {
        "moved": moved,
        "errors": errors,
        "summary": f"Moved {len(moved)} file(s), {len(errors)} error(s).",
    }


# ---------------------------------------------------------------------------
# Config-bound tool factory (used by the ReAct agent)
# ---------------------------------------------------------------------------

def make_configured_tools(ignored_log: str, moved_log: str, retain_copy: bool):
    """
    Return a (scan_tool, move_tool) pair with *ignored_log*, *moved_log*, and
    *retain_copy* already baked in.  The LLM only needs to supply the directory
    paths — it never sees or decides on the config parameters.
    """

    @tool
    def scan_powerpoints_agent(
        directory: Annotated[str, "Absolute path to the root directory to scan for PowerPoint files"],
    ) -> dict:
        """
        Recursively scan *directory* for PowerPoint files (.pptx, .ppt, .pptm).
        Files inside git repositories are excluded.
        Returns a dict with 'found', 'ignored', and 'summary'.
        """
        return _scan_pptx_impl(directory, ignored_log)

    @tool
    def move_powerpoints_agent(
        pptx_paths: Annotated[list[str], "List of absolute PowerPoint file paths to move"],
        destination_directory: Annotated[str, "Absolute path to the destination directory"],
    ) -> dict:
        """
        Move each file in *pptx_paths* to *destination_directory*.
        Returns a dict with 'moved', 'errors', and 'summary'.
        """
        return _move_pptx_impl(pptx_paths, destination_directory, moved_log, retain_copy)

    return scan_powerpoints_agent, move_powerpoints_agent


# ---------------------------------------------------------------------------
# LangChain @tool wrappers (available for future agent-style use)
# ---------------------------------------------------------------------------

@tool
def scan_powerpoints(
    directory: Annotated[str, "Absolute path to the root directory to scan"],
    ignored_log: Annotated[str, "File path where ignored file paths will be written"],
) -> dict:
    """
    Recursively scan *directory* for PowerPoint files (.pptx, .ppt, .pptm).
    Any file found inside a git repository is excluded and recorded in *ignored_log*.
    Returns a dict with 'found', 'ignored', and 'summary'.
    """
    return _scan_pptx_impl(directory, ignored_log)


@tool
def move_powerpoints(
    pptx_paths: Annotated[list[str], "List of absolute PowerPoint file paths to move"],
    destination_directory: Annotated[str, "Absolute path to the destination directory"],
) -> dict:
    """
    Move each file in *pptx_paths* to *destination_directory*.
    Returns a dict with 'moved', 'errors', and 'summary'.
    """
    return _move_pptx_impl(pptx_paths, destination_directory)
