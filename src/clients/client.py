"""
client.py

CLI client for the Desktop Image Organizer API.

Usage examples:
    python client.py                              # use config.yaml defaults
    python client.py --source C:/Users/me/Desktop
    python client.py --dest   C:/Users/me/Pictures/Organized
    python client.py --url http://other-host:8000
"""

import argparse
import json
import sys

import requests

DEFAULT_URL = "http://localhost:8000"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send an organize request to the Desktop Image Organizer API."
    )
    parser.add_argument("--source",      metavar="DIR",  help="Source directory to scan (overrides config.yaml)")
    parser.add_argument("--dest",        metavar="DIR",  help="Destination directory for images (overrides config.yaml)")
    parser.add_argument("--ignored-log", metavar="FILE", help="Path for ignored-images log (overrides config.yaml)")
    parser.add_argument("--url",         default=DEFAULT_URL, help=f"API base URL (default: {DEFAULT_URL})")
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

    print("Sending organize request to", args.url)
    if payload:
        print("Overrides:", json.dumps(payload, indent=2))
    else:
        print("No overrides — using config.yaml defaults.")
    print()

    # --- call the API (long timeout: the LLM + file ops can take a while) ---
    try:
        resp = requests.post(f"{args.url}/organize", json=payload, timeout=600)
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
    print(f"\nAgent summary:\n{data['agent_summary']}")


if __name__ == "__main__":
    main()
