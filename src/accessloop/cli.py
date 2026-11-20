"""Command line entry points for the offline demo and browser evidence."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .browser import inspect_page


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="accessloop")
    sub = parser.add_subparsers(dest="command", required=True)
    inspect = sub.add_parser("inspect", help="collect read-only page and keyboard-focus evidence")
    inspect.add_argument("url")
    inspect.add_argument("--tabs", type=int, default=12)
    inspect.add_argument("--screenshot", help="optional local image path; may contain sensitive information")
    args = parser.parse_args(argv)
    if args.command == "inspect":
        print(json.dumps(asdict(inspect_page(args.url, tabs=args.tabs, screenshot=args.screenshot)), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
