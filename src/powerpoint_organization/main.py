"""
main.py

Entry point for the PowerPoint organizer.
Reads config/config.yaml and kicks off the LangGraph workflow.
"""

import sys
from pathlib import Path

import yaml

# Ensure src/ is on sys.path so package imports work when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from powerpoint_organization.workflow import run_workflow

# Resolve config path relative to this file so it works regardless of working directory.
# src/powerpoint_organization/main.py -> parent -> powerpoint_organization/ -> parent -> src/ -> parent -> project root
_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "config.yaml"


def load_config() -> dict:
    if not _CONFIG_PATH.exists():
        print(f"Error: config file not found at '{_CONFIG_PATH}'")
        sys.exit(1)
    with _CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def main() -> None:
    config = load_config()

    source_dir  = config.get("powerpoint_source_directory", "").strip()
    dest_dir    = config.get("powerpoint_destination_directory", "").strip()
    ignored_log = config.get("powerpoint_ignored_log", "powerpoint_ignored.log").strip()
    moved_log   = config.get("powerpoint_moved_log", "powerpoint_moved.log").strip()
    retain_copy = bool(config.get("powerpoint_retain_copy", False))
    use_agent   = bool(config.get("use_agent", False))

    model_cfg   = config.get("model", {})
    model_name  = model_cfg.get("name", "llama3.2")
    temperature = float(model_cfg.get("temperature", 0.0))

    if not source_dir or not dest_dir:
        print("Error: 'powerpoint_source_directory' and 'powerpoint_destination_directory' must be set in config.yaml")
        sys.exit(1)

    print(f"Source      : {source_dir}")
    print(f"Destination : {dest_dir}")
    print(f"Ignored log : {ignored_log}")
    print(f"Moved log   : {moved_log}")
    print(f"Retain copy : {retain_copy}")
    print(f"Use agent   : {use_agent}")
    print(f"Model       : {model_name}  (temperature={temperature})")
    print("-" * 60)

    response = run_workflow(
        source_dir=source_dir,
        destination_dir=dest_dir,
        ignored_log=ignored_log,
        moved_log=moved_log,
        retain_copy=retain_copy,
        use_agent=use_agent,
        model_name=model_name,
        temperature=temperature,
    )

    print("\n=== Agent summary ===")
    print(response)


if __name__ == "__main__":
    main()
