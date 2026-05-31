#!/usr/bin/env python3
"""Validate many JSON files in one Python process."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def iter_paths(args: argparse.Namespace) -> list[Path]:
    paths = [Path(path) for path in args.paths]
    if args.stdin0:
        raw = sys.stdin.buffer.read()
        paths.extend(Path(item.decode("utf-8")) for item in raw.split(b"\0") if item)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin0", action="store_true", help="read NUL-delimited paths from stdin")
    parser.add_argument("paths", nargs="*", help="JSON files to validate")
    args = parser.parse_args()

    failures: list[str] = []
    for path in iter_paths(args):
        try:
            with path.open("r", encoding="utf-8") as handle:
                json.load(handle)
        except Exception as exc:  # noqa: BLE001 - report parse and IO failures uniformly.
            failures.append(f"{path}: {exc}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
