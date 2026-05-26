#!/usr/bin/env python3
"""Validate Gate 5 statistics and adjudication scaffold boundaries."""

from __future__ import annotations

import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ADJUDICATION_FORM = REPO_ROOT / "paper" / "gate5-adjudication-form.md"
STATISTICS_PLAN = REPO_ROOT / "paper" / "gate5-statistics-plan.md"

REQUIRED_PHRASES = {
    ADJUDICATION_FORM: [
        "Status: scaffold only.",
        "No Gate 5 human adjudication has been completed",
        "Do not invent reviewer",
        "Do not compute percent agreement, Cohen's kappa",
    ],
    STATISTICS_PLAN: [
        "Status: plan and scaffold only.",
        "No Gate 5 full-paper statistics",
        "Do not populate this schema with placeholder numerical results.",
        "Gate 5 remains open",
    ],
}

PROHIBITED_PATTERNS = [
    re.compile(r"\bGate 5 (?:is )?complete\b", re.IGNORECASE),
    re.compile(r"\bfull-paper statistics (?:are|were) complete\b", re.IGNORECASE),
    re.compile(r"\b(?:percent agreement|Cohen'?s kappa|kappa)\s*(?:=|:)\s*\d", re.IGNORECASE),
    re.compile(r"\b(?:Wilson|bootstrap|confidence) interval\s*(?:=|:)\s*[\[(]?\d", re.IGNORECASE),
    re.compile(r"\breviewer agreement\s*(?:=|:)\s*\d", re.IGNORECASE),
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_required_phrases(path: Path, text: str) -> None:
    for phrase in REQUIRED_PHRASES[path]:
        require(phrase in text, f"{path.relative_to(REPO_ROOT)} missing required phrase: {phrase}")


def validate_no_fake_results(path: Path, text: str) -> None:
    for pattern in PROHIBITED_PATTERNS:
        match = pattern.search(text)
        if match is not None:
            raise AssertionError(
                f"{path.relative_to(REPO_ROOT)} contains prohibited result-like text: {match.group(0)}"
            )


def main() -> int:
    for path in (ADJUDICATION_FORM, STATISTICS_PLAN):
        require(path.is_file(), f"missing Gate 5 scaffold: {path.relative_to(REPO_ROOT)}")
        text = path.read_text(encoding="utf-8")
        validate_required_phrases(path, text)
        validate_no_fake_results(path, text)

    print("Gate 5 scaffolds validated: plan-only, no completed statistics or reviewer agreement")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Gate 5 scaffold validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
