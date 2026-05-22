#!/usr/bin/env python3
"""Replace machine-local paths in publishable text artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_TARGETS = (
    "results/raw",
    "results/mvp",
)
SKIP_SUFFIXES = {
    ".pyc",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
    ".docx",
    ".zip",
    ".gz",
}


def iter_text_files(root: Path, targets: list[str]) -> list[Path]:
    files: list[Path] = []
    for target in targets:
        path = root / target
        if not path.exists():
            continue
        if path.is_file():
            files.append(path)
            continue
        for child in sorted(path.rglob("*")):
            if child.is_file() and child.suffix.lower() not in SKIP_SUFFIXES:
                files.append(child)
    return files


def scrub_file(path: Path, replacements: list[tuple[str, str]]) -> bool:
    try:
        original = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False
    scrubbed = original
    for source, replacement in replacements:
        if source:
            scrubbed = scrubbed.replace(source, replacement)
    if scrubbed == original:
        return False
    path.write_text(scrubbed, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--target", action="append", default=[])
    parser.add_argument("--source-root", action="append", default=[])
    args = parser.parse_args()

    root = args.root.resolve()
    targets = args.target or list(DEFAULT_TARGETS)
    replacements = [(str(root), "<REPO_ROOT>")]
    for source_root in args.source_root:
        replacements.append((str(Path(source_root).resolve()), "<LOCAL_SOURCE_CHECKOUT>"))

    changed = 0
    for path in iter_text_files(root, targets):
        changed += int(scrub_file(path, replacements))
    print(f"scrubbed local paths in {changed} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
