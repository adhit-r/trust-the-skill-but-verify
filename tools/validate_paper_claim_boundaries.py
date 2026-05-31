#!/usr/bin/env python3
"""Validate paper-facing claim-boundary prose.

This validator is intentionally narrow. It catches stale gate wording and
high-risk unsupported claim upgrades that are easy to reintroduce while moving
draft prose into the manuscript.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_TEXT = {
    "paper/method-boundaries.md": [
        "## Machine-Only Release Boundary",
        "## Reviewer Objection Responses",
        "The current artifact-release path is a curated local machine-only bundle.",
        "Completed human/manual review remains zero.",
        "They do not support defense-success claims.",
    ],
    "paper/tables/evidence-boundary-matrix.md": [
        "| Related work and venue positioning | Promoted bounded evidence |",
        "| Artifact release package | Promoted bounded evidence |",
        "public release readiness, external review completion, raw scratch publication, completed human review, or paper-grade completion",
    ],
    "paper/figures.md": [
        "public release readiness, external review completion, or whole-repo archive readiness",
    ],
    "docs/research/research-todo.md": [
        "5. [x] Add reviewer-objection answers directly in the methodology and",
        "6. [x] Keep limitations explicit: no real secrets, no live SaaS exports, no",
        "tools/validate_paper_claim_boundaries.py",
    ],
    "scripts/verify_all.sh": [
        "tools/validate_paper_claim_boundaries.py",
    ],
}

FORBIDDEN_PATTERNS = [
    r"\bthis is the first\b",
    r"\bfirst benchmark\b",
    r"\bartifact-ready benchmark\b",
    r"\bpaper-ready benchmark\b",
    r"\bhuman-validated findings\b",
    r"\breview-backed findings\b",
    r"\bcompleted human review exists\b",
    r"\bhuman review complete\b",
    r"\breviewer agreement is complete\b",
    r"\bpublic release ready\b",
    r"\bexternal review complete\b",
    r"\bwhole-repo archive is release-ready\b",
    r"\bSemia equivalence is supported\b",
    r"\bcommercial-runtime coverage is supported\b",
    r"\bRP6 proves defense success\b",
]

SCAN_PATHS = [
    "README.md",
    "docs/artifact",
    "docs/research",
    "paper",
]


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    for relative in SCAN_PATHS:
        path = REPO_ROOT / relative
        if path.is_file() and path.suffix == ".md":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(path.rglob("*.md")))
    return sorted({path.resolve() for path in files})


def validate_required_text() -> list[str]:
    errors: list[str] = []
    for relative_path, required_items in REQUIRED_TEXT.items():
        path = REPO_ROOT / relative_path
        if not path.is_file():
            errors.append(f"missing required file: {relative_path}")
            continue
        text = path.read_text(encoding="utf-8")
        for required in required_items:
            if required not in text:
                errors.append(f"{relative_path}: missing required boundary text: {required!r}")
    return errors


def validate_forbidden_patterns() -> list[str]:
    errors: list[str] = []
    compiled = [re.compile(pattern, re.IGNORECASE) for pattern in FORBIDDEN_PATTERNS]
    for path in iter_markdown_files():
        relative_path = path.relative_to(REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            for pattern in compiled:
                if pattern.search(line):
                    errors.append(f"{relative_path}:{line_no}: forbidden claim-upgrade phrase: {line.strip()}")
    return errors


def validate_stale_rows() -> list[str]:
    text = read("paper/tables/evidence-boundary-matrix.md")
    errors: list[str] = []
    stale = [
        "| Related work and venue positioning | Future work |",
        "| Artifact release package | Future work |",
        "release-bundle completion before the bundle is built and tested",
    ]
    for phrase in stale:
        if phrase in text or phrase in read("paper/figures.md"):
            errors.append(f"stale boundary phrase still present: {phrase!r}")
    return errors


def main() -> int:
    errors = [
        *validate_required_text(),
        *validate_forbidden_patterns(),
        *validate_stale_rows(),
    ]
    if errors:
        print("paper claim-boundary validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print("validated paper claim boundaries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
