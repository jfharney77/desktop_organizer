"""
log_utils.py

Shared log-file utilities used by all organizer packages.
"""

import shutil
from datetime import datetime
from pathlib import Path


def archive_if_exists(log_path: Path) -> None:
    """
    If *log_path* exists and has content, copy it to a timestamped archive
    file in the same directory before the caller overwrites or recreates it.

    Archive name format:  <stem>-<YYYYMMDD-HHMMSS><suffix>
    Example:  moved_images.log  →  moved_images-20260314-153042.log
    """
    if log_path.exists() and log_path.stat().st_size > 0:
        timestamp    = datetime.now().strftime("%Y%m%d-%H%M%S")
        archive_path = log_path.with_name(f"{log_path.stem}-{timestamp}{log_path.suffix}")
        shutil.copy2(log_path, archive_path)
