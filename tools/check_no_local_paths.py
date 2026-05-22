#!/usr/bin/env python3
"""Fail when tracked publishable artifacts contain machine-local paths."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


DEFAULT_PATTERNS = [
    r"/Users/[^/\s\"']+",
    r"/private/var/folders/[^\s\"']+",
    r"/var/folders/[^\s\"']+",
]

SKIP_SUFFIXES = {
    ".docx",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".zip",
    ".gz",
}
SKIP_RELATIVE_PATHS = {
    Path("tools/check_no_local_paths.py"),
}


def git_files(root: Path) -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [root / item.decode() for item in completed.stdout.split(b"\0") if item]


def is_skipped(path: Path) -> bool:
    return path.suffix.lower() in SKIP_SUFFIXES


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--pattern",
        action="append",
        default=[],
        help="Additional regular expression to treat as a forbidden local path.",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    patterns = [re.compile(pattern) for pattern in [*DEFAULT_PATTERNS, *args.pattern]]
    findings: list[tuple[Path, int, str]] = []

    for path in git_files(root):
        rel_path = path.relative_to(root)
        if rel_path in SKIP_RELATIVE_PATHS or is_skipped(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if any(pattern.search(line) for pattern in patterns):
                findings.append((rel_path, line_no, line.strip()))

    if findings:
        print("tracked local path leakage detected:", file=sys.stderr)
        for rel_path, line_no, line in findings:
            print(f"{rel_path}:{line_no}: {line}", file=sys.stderr)
        return 1

    print("no tracked local host path leakage found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
