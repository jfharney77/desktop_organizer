"""
stream_utils.py

Async generator helpers that move files/directories one at a time and yield
progress dicts.  Used by the SSE streaming endpoints in api.py.

Yielded event shapes
--------------------
  {"type": "scanning"}
  {"type": "scan_complete", "total": N}
  {"type": "progress", "current": N, "total": N, "percent": N, "name": "..."}
  {"type": "complete", "moved": N, "errors": N, "summary": "..."}
  {"type": "error", "message": "..."}
"""

import asyncio
import shutil
from datetime import datetime
from pathlib import Path

from log_utils import archive_if_exists


def _resolve_dest(dest: Path, name: str, is_dir: bool = False) -> Path:
    """Return a non-conflicting destination path, appending _1, _2, … as needed."""
    candidate = dest / name
    if not candidate.exists():
        return candidate
    stem   = Path(name).stem
    suffix = "" if is_dir else Path(name).suffix
    counter = 1
    while candidate.exists():
        candidate = dest / f"{stem}_{counter}{suffix}"
        counter += 1
    return candidate


def _write_log(log_path: Path, log_rows: list) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    archive_if_exists(log_path)
    with log_path.open("w", encoding="utf-8") as fh:
        fh.write("| Name | Original Location | New Location | Date of Move | Copy Retained |\n")
        fh.write("|------|-------------------|--------------|--------------|---------------|\n")
        for name, orig, new, date, copy in log_rows:
            fh.write(f"| {name} | {orig} | {new} | {date} | {copy} |\n")


async def stream_move_files(
    paths: list[str],
    destination_directory: str,
    moved_log: str = "",
    retain_copy: bool = False,
):
    """Async generator — yields progress events as each file is moved."""
    dest = Path(destination_directory)
    dest.mkdir(parents=True, exist_ok=True)
    total = len(paths)
    moved, errors = 0, 0
    log_rows = []

    for i, src_str in enumerate(paths):
        src = Path(src_str)
        if not src.exists():
            errors += 1
            yield {"type": "progress", "current": i + 1, "total": total,
                   "percent": round((i + 1) / total * 100),
                   "name": src.name, "error": f"Not found: {src_str}"}
            await asyncio.sleep(0)
            continue

        dest_file = _resolve_dest(dest, src.name)
        try:
            if retain_copy:
                shutil.copy2(str(src), str(dest_file))
            else:
                shutil.move(str(src), str(dest_file))
            moved += 1
            log_rows.append((
                src.name, str(src), str(dest_file),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Yes" if retain_copy else "No",
            ))
        except Exception as exc:
            errors += 1
            yield {"type": "progress", "current": i + 1, "total": total,
                   "percent": round((i + 1) / total * 100),
                   "name": src.name, "error": str(exc)}
            await asyncio.sleep(0)
            continue

        yield {"type": "progress", "current": i + 1, "total": total,
               "percent": round((i + 1) / total * 100), "name": src.name}
        await asyncio.sleep(0)

    if log_rows and moved_log:
        _write_log(Path(moved_log), log_rows)

    yield {"type": "complete", "moved": moved, "errors": errors,
           "summary": f"Moved {moved} file(s), {errors} error(s)."}


async def stream_move_dirs(
    paths: list[str],
    destination_directory: str,
    moved_log: str = "",
    retain_copy: bool = False,
):
    """Async generator — yields progress events as each directory is moved."""
    dest = Path(destination_directory)
    dest.mkdir(parents=True, exist_ok=True)
    total = len(paths)
    moved, errors = 0, 0
    log_rows = []

    for i, src_str in enumerate(paths):
        src = Path(src_str)
        if not src.exists() or not src.is_dir():
            errors += 1
            yield {"type": "progress", "current": i + 1, "total": total,
                   "percent": round((i + 1) / total * 100),
                   "name": src.name, "error": f"Not found: {src_str}"}
            await asyncio.sleep(0)
            continue

        dest_dir = _resolve_dest(dest, src.name, is_dir=True)
        try:
            if retain_copy:
                shutil.copytree(str(src), str(dest_dir))
            else:
                shutil.move(str(src), str(dest_dir))
            moved += 1
            log_rows.append((
                src.name, str(src), str(dest_dir),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Yes" if retain_copy else "No",
            ))
        except Exception as exc:
            errors += 1
            yield {"type": "progress", "current": i + 1, "total": total,
                   "percent": round((i + 1) / total * 100),
                   "name": src.name, "error": str(exc)}
            await asyncio.sleep(0)
            continue

        yield {"type": "progress", "current": i + 1, "total": total,
               "percent": round((i + 1) / total * 100), "name": src.name}
        await asyncio.sleep(0)

    if log_rows and moved_log:
        _write_log(Path(moved_log), log_rows)

    yield {"type": "complete", "moved": moved, "errors": errors,
           "summary": f"Moved {moved} director{'y' if moved == 1 else 'ies'}, {errors} error(s)."}
