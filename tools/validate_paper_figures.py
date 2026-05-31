#!/usr/bin/env python3
"""Validate the paper figure package."""

from __future__ import annotations

import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "paper" / "figures" / "manifest.json"
CLAIM_LEDGER_PATH = REPO_ROOT / "paper" / "claim-ledger.json"
REQUIRED_FIGURES = {
    "F1": "fig1-architecture.svg",
    "F2": "fig2-trace-lifecycle.svg",
    "F3": "fig3-runtime-matrix.svg",
    "F4": "fig4-drift-outcomes.svg",
    "F5": "fig5-runtime-report-cards.svg",
    "F6": "fig6-artifact-flow.svg",
}
REQUIRED_BOUNDARY_FLAGS = {
    "adds_new_experimental_results": False,
    "prevalence_claim": False,
    "commercial_runtime_claim": False,
    "public_network_exfiltration_claim": False,
    "syscall_complete_tracing_claim": False,
    "defense_success_claim": False,
    "completed_human_review_claim": False,
}


class SVGStructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.svg_count = 0
        self.title_count = 0
        self.desc_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "svg":
            self.svg_count += 1
        elif tag == "title":
            self.title_count += 1
        elif tag == "desc":
            self.desc_count += 1


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def repo_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        raise AssertionError(f"figure manifest path must be relative: {value}")
    return REPO_ROOT / path


def validate_svg(path: Path) -> None:
    if path.suffix != ".svg":
        raise AssertionError(f"{path}: expected .svg asset")
    text = path.read_text(encoding="utf-8")
    if not text.lstrip().startswith("<svg"):
        raise AssertionError(f"{path}: file must start with <svg")
    if not text.rstrip().endswith("</svg>"):
        raise AssertionError(f"{path}: file must end with </svg>")
    parser = SVGStructureParser()
    parser.feed(text)
    if parser.svg_count != 1:
        raise AssertionError(f"{path}: expected one svg root, found {parser.svg_count}")
    if parser.title_count < 1:
        raise AssertionError(f"{path}: missing title accessibility element")
    if parser.desc_count < 1:
        raise AssertionError(f"{path}: missing desc accessibility element")


def main() -> int:
    manifest = load_json(MANIFEST_PATH)
    figures = manifest.get("figures")
    if not isinstance(figures, list):
        raise AssertionError("manifest.figures must be a list")
    if len(figures) != len(REQUIRED_FIGURES):
        raise AssertionError(f"expected {len(REQUIRED_FIGURES)} figures, found {len(figures)}")

    ledger = load_json(CLAIM_LEDGER_PATH)
    claim_ids = {claim["claim_id"] for claim in ledger.get("claims", [])}

    seen: set[str] = set()
    for figure in figures:
        figure_id = figure.get("figure_id")
        if figure_id not in REQUIRED_FIGURES:
            raise AssertionError(f"unexpected figure_id: {figure_id!r}")
        if figure_id in seen:
            raise AssertionError(f"duplicate figure_id: {figure_id}")
        seen.add(figure_id)

        asset_value = figure.get("asset")
        if not isinstance(asset_value, str):
            raise AssertionError(f"{figure_id}: asset must be a string")
        asset_path = repo_path(asset_value)
        if asset_path.name != REQUIRED_FIGURES[figure_id]:
            raise AssertionError(f"{figure_id}: expected asset {REQUIRED_FIGURES[figure_id]}")
        if not asset_path.is_file():
            raise FileNotFoundError(asset_path)
        validate_svg(asset_path)

        for source in figure.get("source_paths", []):
            if not repo_path(source).exists():
                raise FileNotFoundError(f"{figure_id}: missing source path {source}")
        for claim_id in figure.get("claim_ids", []):
            if claim_id not in claim_ids:
                raise AssertionError(f"{figure_id}: unknown claim_id {claim_id}")
        if figure.get("numeric_fields") != []:
            raise AssertionError(f"{figure_id}: numeric_fields must stay empty until generated from claims")
        if figure.get("regen_command") != "manual-svg":
            raise AssertionError(f"{figure_id}: unexpected regen_command")

    if seen != set(REQUIRED_FIGURES):
        raise AssertionError(f"missing figures: {sorted(set(REQUIRED_FIGURES) - seen)}")

    boundary = manifest.get("claim_boundary")
    if boundary != REQUIRED_BOUNDARY_FLAGS:
        raise AssertionError("figure manifest claim_boundary does not match required false-claim flags")

    print(f"validated paper figure package: {len(figures)} SVG figure(s)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"paper figure validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
