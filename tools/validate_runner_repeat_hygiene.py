#!/usr/bin/env python3
"""Validate repeat-ID plumbing in top-level runner wrappers."""

from __future__ import annotations

import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_GLOB = "run_*.py"
ALLOWED_HARDCODED_REPEAT_FILES = {
    "run_main_rp2_rp3_repeat_stability.py",
    "run_planned_inclusion_repeat_stability.py",
}


def has_child_repeat_argument(text: str) -> bool:
    return '"--repeat-id"' in text


def has_repeat_cli(text: str) -> bool:
    return "add_repeat_id_argument(parser)" in text or 'parser.add_argument("--repeat-id"' in text


def has_hardcoded_trace_context(text: str) -> bool:
    return bool(re.search(r"repeat_id\s*=\s*(?:1\b|[\"']1[\"'])", text))


def has_hardcoded_child_repeat(text: str) -> bool:
    return bool(re.search(r'"--repeat-id"\s*,\s*\n\s*"1"', text))


def main() -> int:
    failures: list[str] = []
    for path in sorted((REPO_ROOT / "tools").glob(RUNNER_GLOB)):
        text = path.read_text(encoding="utf-8")
        name = path.name
        if name in ALLOWED_HARDCODED_REPEAT_FILES:
            continue
        if has_child_repeat_argument(text) and not has_repeat_cli(text):
            failures.append(f"{path.relative_to(REPO_ROOT)} passes --repeat-id but exposes no runner --repeat-id")
        if has_hardcoded_child_repeat(text):
            failures.append(f"{path.relative_to(REPO_ROOT)} hard-codes child --repeat-id 1")
        if has_hardcoded_trace_context(text):
            failures.append(f"{path.relative_to(REPO_ROOT)} hard-codes TraceContext repeat_id=1")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("validated runner repeat-ID hygiene")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
