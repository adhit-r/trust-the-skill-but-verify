#!/usr/bin/env python3
"""Convert a completed Gate 5 human-review worksheet CSV into review-export JSON."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSHEET = REPO_ROOT / "benchmark" / "review" / "gate5-reviewer-a-worksheet.csv"
DEFAULT_TEMPLATE_PACKAGE = REPO_ROOT / "benchmark" / "review" / "gate5-review-export-templates.json"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import build_gate5_human_review_worksheet  # noqa: E402
import build_gate5_review_packet_index  # noqa: E402
import validate_gate5_completed_review_export  # noqa: E402


TIMESTAMP_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames == build_gate5_human_review_worksheet.FIELDNAMES, "worksheet header mismatch")
        return [dict(row) for row in reader]


def parse_bool(value: str, *, item_id: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise AssertionError(f"{item_id}: paper_claimable must be true or false")


def clean_optional(value: str) -> str | None:
    stripped = value.strip()
    return stripped if stripped else None


def validate_enum(row: dict[str, str], column: str) -> str:
    value = row[column].strip()
    allowed = build_gate5_human_review_worksheet.ALLOWED_VALUES[column]
    require(value in allowed, f"{row['review_item_id']}: {column} must be one of {allowed}")
    return value


def build_response(row: dict[str, str]) -> dict[str, Any]:
    response_status = validate_enum(row, "response_status")
    paper_claimable = parse_bool(row["paper_claimable"], item_id=row["review_item_id"])
    exclusion_reason = clean_optional(row["exclusion_reason"])
    evidence_summary = row["evidence_summary"].strip()
    uncertainty_or_notes = clean_optional(row["uncertainty_or_notes"])
    require(evidence_summary, f"{row['review_item_id']}: evidence_summary is required")
    if paper_claimable:
        require(exclusion_reason is None, f"{row['review_item_id']}: claimable rows must leave exclusion_reason empty")
    else:
        require(exclusion_reason is not None, f"{row['review_item_id']}: non-claimable rows need exclusion_reason")
    return {
        "response_status": response_status,
        "finding_kind": validate_enum(row, "finding_kind"),
        "drift_class": validate_enum(row, "drift_class"),
        "severity": validate_enum(row, "severity"),
        "task_success": validate_enum(row, "task_success"),
        "expected_output_status": validate_enum(row, "expected_output_status"),
        "canary_status": validate_enum(row, "canary_status"),
        "paper_claimable": paper_claimable,
        "exclusion_reason": exclusion_reason,
        "evidence_summary": evidence_summary,
        "uncertainty_or_notes": uncertainty_or_notes,
    }


def build_export(
    *,
    worksheet_path: Path,
    template_package_path: Path,
    reviewer_slot: str,
    reviewer_id: str,
    review_timestamp_utc: str,
) -> dict[str, Any]:
    require(TIMESTAMP_RE.match(review_timestamp_utc) is not None, "review timestamp must be YYYY-MM-DDTHH:MM:SSZ")
    package = load_json(template_package_path)
    template = build_gate5_human_review_worksheet.select_template(package, reviewer_slot)
    expected_blank_rows = build_gate5_human_review_worksheet.build_rows(template_package_path, reviewer_slot)
    rows = read_rows(worksheet_path)
    require(len(rows) == len(expected_blank_rows), "worksheet row count mismatch")

    review_items: list[dict[str, Any]] = []
    for row, expected, template_item in zip(rows, expected_blank_rows, template["review_items"], strict=True):
        for column in build_gate5_human_review_worksheet.CONTEXT_COLUMNS:
            require(row[column] == expected[column], f"{row.get('review_item_id', '<unknown>')}: context column changed: {column}")
        review_items.append(
            {
                "review_item_id": template_item["review_item_id"],
                "packet_id": template_item["packet_id"],
                "unit_id": template_item["unit_id"],
                "unit_type": template_item["unit_type"],
                "response": build_response(row),
            }
        )

    bundle_path = REPO_ROOT / package["input_refs"]["blinded_packet_bundle_ref"]
    return {
        "schema_version": "0.1",
        "export_id": f"gate5-{reviewer_slot}-completed-review-{reviewer_id}",
        "export_kind": "completed_human_review_export",
        "export_status": "completed_human_review",
        "review_pass": "first_pass_blinded_pair_review",
        "reviewer": {
            "reviewer_id": reviewer_id,
            "reviewer_kind": "real_human",
            "review_timestamp_utc": review_timestamp_utc,
            "codex_assisted": False,
            "counts_as_human_review": True,
        },
        "input_refs": {
            "review_export_templates_ref": template_package_path.relative_to(REPO_ROOT).as_posix(),
            "blinded_packet_bundle_ref": package["input_refs"]["blinded_packet_bundle_ref"],
        },
        "export_lock": {
            "template_export_id": template["export_id"],
            "template_package_sha256": build_gate5_review_packet_index.sha256_file(template_package_path),
            "blinded_packet_bundle_sha256": build_gate5_review_packet_index.sha256_file(bundle_path),
        },
        "claim_boundary": {
            "completed_single_human_review_only": True,
            "reviewer_agreement_claimed": False,
            "adjudication_claimed": False,
            "completed_statistics_claimed": False,
            "prevalence_claim": False,
            "paper_grade_completion_claimed": False,
        },
        "review_items": review_items,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worksheet", type=Path, default=DEFAULT_WORKSHEET)
    parser.add_argument("--template-package", type=Path, default=DEFAULT_TEMPLATE_PACKAGE)
    parser.add_argument("--reviewer-slot", choices=["reviewer_a", "reviewer_b"], required=True)
    parser.add_argument("--reviewer-id", required=True)
    parser.add_argument("--review-timestamp-utc", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    worksheet_path = args.worksheet if args.worksheet.is_absolute() else REPO_ROOT / args.worksheet
    template_package_path = (
        args.template_package if args.template_package.is_absolute() else REPO_ROOT / args.template_package
    )
    output_path = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    export = build_export(
        worksheet_path=worksheet_path,
        template_package_path=template_package_path,
        reviewer_slot=args.reviewer_slot,
        reviewer_id=args.reviewer_id,
        review_timestamp_utc=args.review_timestamp_utc,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(export, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validate_gate5_completed_review_export.validate_completed_export(output_path)
    print(output_path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Gate 5 worksheet conversion failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
