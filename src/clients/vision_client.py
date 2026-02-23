"""
vision_client.py

CLI client for the image description (vision) endpoint.

Usage examples:
    python vision_client.py                                    # use config.yaml defaults
    python vision_client.py --image photo.jpg                  # override image name
    python vision_client.py --image photo.jpg --dir C:/pics    # override image name and search directory
    python vision_client.py --url http://other-host:8001       # point at a remote server
"""

import argparse
import sys
import textwrap

import requests

DEFAULT_URL = "http://localhost:8001"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send a describe request to the Desktop Image Organizer vision API."
    )
    parser.add_argument("--image", metavar="FILE", help="Image filename to describe (overrides config.yaml)")
    parser.add_argument("--dir",   metavar="DIR",  help="Directory to search for the image (overrides config.yaml)")
    parser.add_argument("--url",   default=DEFAULT_URL, help=f"API base URL (default: {DEFAULT_URL})")
    args = parser.parse_args()

    # --- health check ---
    try:
        resp = requests.get(f"{args.url}/health", timeout=5)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        print(f"[error] Cannot connect to {args.url}. Is the vision server running?")
        sys.exit(1)

    # --- build payload (only send overrides) ---
    payload: dict = {}
    if args.image:
        payload["image_name"] = args.image
    if args.dir:
        payload["search_directory"] = args.dir

    print("Sending describe request to", args.url)
    if payload:
        print("Overrides:")
        if "image_name" in payload:
            print(f"  Image     : {payload['image_name']}")
        if "search_directory" in payload:
            print(f"  Directory : {payload['search_directory']}")
    else:
        print("No overrides — using config.yaml defaults.")
    print()

    # --- call the API (long timeout: vision model inference can be slow) ---
    try:
        resp = requests.post(f"{args.url}/describe", json=payload, timeout=300)
    except requests.exceptions.ReadTimeout:
        print("[error] Request timed out. The vision model is still running server-side.")
        sys.exit(1)

    if resp.status_code != 200:
        print(f"[error] {resp.status_code}: {resp.text}")
        sys.exit(1)

    data = resp.json()
    print("=== Result ===")
    print(f"Image       : {data['image_name']}")
    print(f"Directory   : {data['search_directory']}")
    print(f"Found       : {data['found']}")

    if data.get("image_path"):
        print(f"Full path   : {data['image_path']}")

    if data.get("error"):
        print(f"\n[error] {data['error']}")
        sys.exit(1)

    print("\nDescription:")
    print(textwrap.fill(data["description"], width=80, initial_indent="  ", subsequent_indent="  "))


if __name__ == "__main__":
    main()
