#!/usr/bin/env python3
"""Validate the blank Gate 5 human-review worksheet artifact."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSHEET = REPO_ROOT / "benchmark" / "review" / "gate5-reviewer-a-worksheet.csv"
DEFAULT_TEMPLATE_PACKAGE = REPO_ROOT / "benchmark" / "review" / "gate5-review-export-templates.json"
DEFAULT_REVIEWER_SLOT = "reviewer_a"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import build_gate5_human_review_worksheet  # noqa: E402
import validate_gate5_review_export_templates  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames == build_gate5_human_review_worksheet.FIELDNAMES, "worksheet header mismatch")
        return [dict(row) for row in reader]


def validate_worksheet(worksheet_path: Path, template_package_path: Path, reviewer_slot: str) -> None:
    validate_gate5_review_export_templates.validate_package(template_package_path)
    require(worksheet_path.is_file(), "missing worksheet CSV")
    markdown_path = worksheet_path.with_suffix(".md")
    require(markdown_path.is_file(), "missing worksheet Markdown guide")

    observed_rows = read_csv(worksheet_path)
    expected_rows = build_gate5_human_review_worksheet.build_rows(template_package_path, reviewer_slot)
    require(observed_rows == expected_rows, "worksheet CSV is stale or no longer blank")
    require(len(observed_rows) == 122, "reviewer worksheet must cover 122 pair-review units")

    markdown = markdown_path.read_text(encoding="utf-8")
    expected_markdown = build_gate5_human_review_worksheet.render_markdown(
        package_path=template_package_path,
        reviewer_slot=reviewer_slot,
        output_csv_path=worksheet_path,
        item_count=len(expected_rows),
    )
    require(markdown == expected_markdown, "worksheet Markdown guide is stale")
    for required in (
        "Status: blank worksheet only. This file is not completed human review evidence.",
        "Assigned pair-review units: `122`",
        "Codex-assisted labels must not be counted as human review evidence.",
        "python3 tools/convert_gate5_human_review_worksheet.py",
        "python3 tools/validate_gate5_completed_review_export.py",
    ):
        require(required in markdown, f"worksheet guide missing: {required}")

    scan_findings = validate_gate5_review_export_templates.scan_text_artifact(worksheet_path)
    scan_findings.extend(validate_gate5_review_export_templates.scan_text_artifact(markdown_path))
    require(not scan_findings, f"worksheet hygiene scan failed: {scan_findings[:3]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worksheet", type=Path, default=DEFAULT_WORKSHEET)
    parser.add_argument("--template-package", type=Path, default=DEFAULT_TEMPLATE_PACKAGE)
    parser.add_argument("--reviewer-slot", choices=["reviewer_a", "reviewer_b"], default=DEFAULT_REVIEWER_SLOT)
    args = parser.parse_args(argv)

    worksheet_path = args.worksheet if args.worksheet.is_absolute() else REPO_ROOT / args.worksheet
    template_package_path = (
        args.template_package if args.template_package.is_absolute() else REPO_ROOT / args.template_package
    )
    validate_worksheet(worksheet_path, template_package_path, args.reviewer_slot)
    print(f"validated Gate 5 human-review worksheet: {worksheet_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Gate 5 human-review worksheet validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
