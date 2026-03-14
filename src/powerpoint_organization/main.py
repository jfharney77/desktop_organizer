"""
main.py

Standalone entry point for the PowerPoint organizer.
Reads config/config.yaml and kicks off the LangGraph workflow.
"""

import sys
from pathlib import Path

import yaml

# Ensure src/ is on sys.path so package imports work when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from powerpoint_organization.workflow import run_workflow

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "config.yaml"


def load_config() -> dict:
    if not _CONFIG_PATH.exists():
        print(f"Error: config file not found at '{_CONFIG_PATH}'")
        sys.exit(1)
    with _CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def main() -> None:
    config = load_config()

    pptx_cfg = config.get("powerpoint", {})

    source_dir  = pptx_cfg.get("source_directory", "").strip()
    dest_dir    = pptx_cfg.get("destination_directory", "").strip()
    ignored_log = pptx_cfg.get("ignored_log", "ignored_pptx.log").strip()
    moved_log   = pptx_cfg.get("moved_log", "moved_pptx.log").strip()
    retain_copy = bool(pptx_cfg.get("retain_copy", False))

    if not source_dir or not dest_dir:
        print("Error: 'powerpoint.source_directory' and 'powerpoint.destination_directory' must be set in config.yaml")
        sys.exit(1)

    print(f"Source      : {source_dir}")
    print(f"Destination : {dest_dir}")
    print(f"Ignored log : {ignored_log}")
    print(f"Moved log   : {moved_log}")
    print(f"Retain copy : {retain_copy}")
    print("-" * 60)

    response = run_workflow(
        source_dir=source_dir,
        destination_dir=dest_dir,
        ignored_log=ignored_log,
        moved_log=moved_log,
        retain_copy=retain_copy,
    )

    print("\n=== Agent summary ===")
    print(response)


if __name__ == "__main__":
    main()
