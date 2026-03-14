"""
tools.py

LangChain tools and underlying implementations for text file organization.

Separating _impl from @tool means the StateGraph nodes can call the logic
directly without going through the LLM.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool

from log_utils import archive_if_exists


TXT_EXTENSIONS = {".txt"}


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

def _scan_txt_impl(directory: str, ignored_log: str) -> dict:
    """
    Recursively scan *directory* for text files (.txt).
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
        if file.is_file() and file.suffix.lower() in TXT_EXTENSIONS:
            if _is_in_git_repo(file):
                ignored.append(str(file))
            else:
                found.append(str(file))

    if ignored:
        log_path = Path(ignored_log)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        archive_if_exists(log_path)
        with log_path.open("w", encoding="utf-8") as fh:
            fh.write("\n".join(ignored) + "\n")

    return {
        "found": found,
        "ignored": ignored,
        "summary": (
            f"Found {len(found)} text file(s) to move, "
            f"ignored {len(ignored)} file(s) inside git repos "
            f"(logged to {ignored_log})"
        ),
    }


def _move_txt_impl(
    txt_paths: list[str],
    destination_directory: str,
    moved_log: str = "",
    retain_copy: bool = False,
) -> dict:
    """
    Move (or copy, if *retain_copy* is True) each file in *txt_paths* to
    *destination_directory*.  Numeric suffixes (_1, _2, …) are added on name
    conflicts.  A markdown-table log of every moved file is written to
    *moved_log* (appended if the file already exists).
    """
    dest = Path(destination_directory)
    dest.mkdir(parents=True, exist_ok=True)

    moved: list[str] = []
    errors: list[str] = []
    log_rows: list[tuple[str, str, str, str, str]] = []  # (name, orig, new, date, copy)

    for src_str in txt_paths:
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
        archive_if_exists(log_path)
        with log_path.open("w", encoding="utf-8") as fh:
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
# LangChain @tool wrappers (available for future agent-style use)
# ---------------------------------------------------------------------------

@tool
def scan_txt(
    directory: Annotated[str, "Absolute path to the root directory to scan"],
    ignored_log: Annotated[str, "File path where ignored file paths will be written"],
) -> dict:
    """
    Recursively scan *directory* for text files (.txt).
    Any file found inside a git repository is excluded and recorded in *ignored_log*.
    Returns a dict with 'found', 'ignored', and 'summary'.
    """
    return _scan_txt_impl(directory, ignored_log)


@tool
def move_txt(
    txt_paths: Annotated[list[str], "List of absolute text file paths to move"],
    destination_directory: Annotated[str, "Absolute path to the destination directory"],
) -> dict:
    """
    Move each file in *txt_paths* to *destination_directory*.
    Returns a dict with 'moved', 'errors', and 'summary'.
    """
    return _move_txt_impl(txt_paths, destination_directory)
