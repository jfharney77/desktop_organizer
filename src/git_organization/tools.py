"""
tools.py

LangChain tools and underlying implementations for git repository organization.

A "git repository" is any directory that contains a .git subdirectory.
Scanning walks the source directory and collects every such subdirectory,
stopping recursion once a .git folder is found (no nested-repo traversal).

Moving transfers entire repository directories rather than individual files.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool

from log_utils import archive_if_exists


def is_git_repo(path: Path) -> bool:
    """Return True if *path* is a directory containing a .git folder."""
    return path.is_dir() and (path / ".git").exists()


# ---------------------------------------------------------------------------
# Pure-Python implementations (called directly by StateGraph nodes)
# ---------------------------------------------------------------------------

def _scan_git_repos_impl(directory: str, ignored_log: str) -> dict:
    """
    Walk *directory* for subdirectories that are git repositories.
    Recursion stops when a .git folder is found so nested repos are not
    double-counted.  The source directory itself is never included.
    """
    source = Path(directory)

    if not source.exists():
        return {"error": f"Directory does not exist: {directory}", "found": [], "ignored": []}
    if not source.is_dir():
        return {"error": f"Not a directory: {directory}", "found": [], "ignored": []}

    found: list[str] = []

    for dirpath, dirnames, _ in os.walk(str(source)):
        current = Path(dirpath)
        if current == source:
            continue
        if is_git_repo(current):
            found.append(str(current))
            dirnames.clear()  # prune — do not recurse into this repo

    return {
        "found": found,
        "ignored": [],
        "summary": f"Found {len(found)} git repository/repositories to move.",
    }


def _move_git_repos_impl(
    repo_paths: list[str],
    destination_directory: str,
    moved_log: str = "",
    retain_copy: bool = False,
) -> dict:
    """
    Move (or copy, if *retain_copy* is True) each repository directory in
    *repo_paths* to *destination_directory*.  Numeric suffixes (_1, _2, …)
    are added on name conflicts.  A markdown-table log is written to
    *moved_log*.
    """
    dest = Path(destination_directory)
    dest.mkdir(parents=True, exist_ok=True)

    moved: list[str] = []
    errors: list[str] = []
    log_rows: list[tuple[str, str, str, str, str]] = []

    for src_str in repo_paths:
        src = Path(src_str)

        if not src.exists():
            errors.append(f"Directory not found: {src_str}")
            continue
        if not is_git_repo(src):
            errors.append(f"Not a git repository (no .git folder): {src_str}")
            continue

        dest_dir = dest / src.name

        if dest_dir.exists():
            counter = 1
            while dest_dir.exists():
                dest_dir = dest / f"{src.name}_{counter}"
                counter += 1

        try:
            if retain_copy:
                shutil.copytree(str(src), str(dest_dir))
            else:
                shutil.move(str(src), str(dest_dir))
            moved.append(f"{src_str} -> {dest_dir}")
            log_rows.append((
                src.name,
                str(src),
                str(dest_dir),
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
        "summary": f"Moved {len(moved)} repository/repositories, {len(errors)} error(s).",
    }


# ---------------------------------------------------------------------------
# LangChain @tool wrappers (available for future agent-style use)
# ---------------------------------------------------------------------------

@tool
def scan_git_repos(
    directory: Annotated[str, "Absolute path to the root directory to scan"],
    ignored_log: Annotated[str, "File path where skipped paths will be written"],
) -> dict:
    """
    Recursively scan *directory* for git repositories (directories containing .git).
    Returns a dict with 'found', 'ignored', and 'summary'.
    """
    return _scan_git_repos_impl(directory, ignored_log)


@tool
def move_git_repos(
    repo_paths: Annotated[list[str], "List of absolute git repository directory paths to move"],
    destination_directory: Annotated[str, "Absolute path to the destination directory"],
) -> dict:
    """
    Move each git repository in *repo_paths* to *destination_directory*.
    Returns a dict with 'moved', 'errors', and 'summary'.
    """
    return _move_git_repos_impl(repo_paths, destination_directory)
