"""
powerpoint_client.py

CLI client for the PowerPoint organizer API endpoint.

Usage examples:
    python powerpoint_client.py                                       # use config.yaml defaults
    python powerpoint_client.py --source C:/Users/me/Desktop
    python powerpoint_client.py --dest   C:/Users/me/Documents/Slides
    python powerpoint_client.py --retain-copy
    python powerpoint_client.py --url http://other-host:8000
"""

import argparse
import sys

import requests

DEFAULT_URL = "http://localhost:8002"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send an organize request to the PowerPoint Organizer API."
    )
    parser.add_argument("--source",       metavar="DIR",  help="Source directory to scan (overrides config.yaml)")
    parser.add_argument("--dest",         metavar="DIR",  help="Destination directory for files (overrides config.yaml)")
    parser.add_argument("--ignored-log",  metavar="FILE", help="Path for ignored-files log (overrides config.yaml)")
    parser.add_argument("--moved-log",    metavar="FILE", help="Path for moved-files log (overrides config.yaml)")
    parser.add_argument("--retain-copy",  action="store_true", default=None, help="Keep a copy in the source directory (overrides config.yaml)")
    parser.add_argument("--url",          default=DEFAULT_URL, help=f"API base URL (default: {DEFAULT_URL})")
    args = parser.parse_args()

    # --- health check ---
    try:
        resp = requests.get(f"{args.url}/health", timeout=5)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        print(f"[error] Cannot connect to {args.url}. Is the server running?")
        sys.exit(1)

    # --- build payload (only send overrides) ---
    payload: dict = {}
    if args.source:
        payload["source_directory"] = args.source
    if args.dest:
        payload["destination_directory"] = args.dest
    if args.ignored_log:
        payload["ignored_log"] = args.ignored_log
    if args.moved_log:
        payload["moved_log"] = args.moved_log
    if args.retain_copy:
        payload["retain_copy"] = True

    print("Sending PowerPoint organize request to", args.url)
    if payload:
        print("Overrides:")
        for key, val in payload.items():
            print(f"  {key}: {val}")
    else:
        print("No overrides — using config.yaml defaults.")
    print()

    # --- call the API ---
    try:
        resp = requests.post(f"{args.url}/organize/powerpoint", json=payload, timeout=600)
    except requests.exceptions.ReadTimeout:
        print("[error] Request timed out. The workflow is still running server-side.")
        sys.exit(1)

    if resp.status_code != 200:
        print(f"[error] {resp.status_code}: {resp.text}")
        sys.exit(1)

    data = resp.json()
    print("=== Result ===")
    print(f"Source      : {data['source_directory']}")
    print(f"Destination : {data['destination_directory']}")
    print(f"Ignored log : {data['ignored_log']}")
    print(f"Moved log   : {data['moved_log']}")
    print(f"Retain copy : {data['retain_copy']}")
    print(f"\nAgent summary:\n{data['agent_summary']}")


if __name__ == "__main__":
    main()
