"""
main.py

Entry point for the desktop image organizer.
Reads config/config.yaml and kicks off the LangGraph workflow.
"""

import sys
from pathlib import Path

import yaml

from workflow import run_workflow

# Resolve config path relative to this file so it works regardless of working directory.
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.yaml"


def load_config() -> dict:
    if not _CONFIG_PATH.exists():
        print(f"Error: config file not found at '{_CONFIG_PATH}'")
        sys.exit(1)
    with _CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def main() -> None:
    config = load_config()

    source_dir = config.get("source_directory", "").strip()
    dest_dir = config.get("destination_directory", "").strip()
    ignored_log = config.get("ignored_log", "ignored_images.log").strip()
    moved_log = config.get("moved_log", "moved_images.log").strip()
    retain_copy = bool(config.get("retain_copy", False))

    model_cfg = config.get("model", {})
    model_name = model_cfg.get("name", "llama3.2")
    temperature = float(model_cfg.get("temperature", 0.0))

    if not source_dir or not dest_dir:
        print("Error: 'source_directory' and 'destination_directory' must be set in config.yaml")
        sys.exit(1)

    print(f"Source      : {source_dir}")
    print(f"Destination : {dest_dir}")
    print(f"Ignored log : {ignored_log}")
    print(f"Moved log   : {moved_log}")
    print(f"Retain copy : {retain_copy}")
    print(f"Model       : {model_name}  (temperature={temperature})")
    print("-" * 60)

    response = run_workflow(
        source_dir=source_dir,
        destination_dir=dest_dir,
        ignored_log=ignored_log,
        moved_log=moved_log,
        retain_copy=retain_copy,
        model_name=model_name,
        temperature=temperature,
    )

    print("\n=== Agent summary ===")
    print(response)


if __name__ == "__main__":
    main()
