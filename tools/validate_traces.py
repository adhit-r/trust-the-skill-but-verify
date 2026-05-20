#!/usr/bin/env python3
"""Validate SkillDiff trace JSONL files."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from skilldiff.traces import TraceValidationError, validate_trace_file  # noqa: E402


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: validate_traces.py TRACE.jsonl [...]", file=sys.stderr)
        return 2
    total = 0
    for raw_path in argv:
        path = Path(raw_path)
        try:
            events = validate_trace_file(path)
        except TraceValidationError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        total += len(events)
        print(f"ok {path} {len(events)} event(s)")
    print(f"validated {len(argv)} trace file(s), {total} event(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
