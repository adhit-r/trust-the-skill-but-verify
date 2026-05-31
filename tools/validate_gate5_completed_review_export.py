#!/usr/bin/env python3
"""Validate one future Gate 5 completed human-review export."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPORT = REPO_ROOT / "benchmark" / "review" / "gate5-completed-review-export.json"
SCHEMA_PATH = REPO_ROOT / "schemas" / "gate5_completed_review_export.schema.json"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import build_gate5_review_packet_index  # noqa: E402
import validate_benchmark_cases  # noqa: E402
import validate_gate5_review_export_templates  # noqa: E402


BLOCKED_REVIEWER_ID_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"tbd",
        r"todo",
        r"placeholder",
        r"codex",
        r"agent",
        r"synthetic",
        r"anonymous",
        r"fake",
        r"dummy",
        r"test",
    )
]
PROHIBITED_AGREEMENT_KEYS = {
    "reviewer_ids_compared",
    "adjudicator_id",
    "adjudication_timestamp_utc",
    "initial_agreement",
    "percent_agreement",
    "cohens_kappa",
    "kappa",
    "wilson_interval",
    "bootstrap_interval",
    "confidence_interval",
    "mcnemar",
    "p_value",
    "resolved_finding_kind",
    "resolved_drift_class",
    "resolved_severity",
    "resolved_paper_claimable",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def repo_path(ref: str | None) -> Path | None:
    if not isinstance(ref, str) or not ref:
        return None
    return REPO_ROOT / ref.split("#", 1)[0]


def validate_schema(export: dict[str, Any], path: Path) -> None:
    schema = load_json(SCHEMA_PATH)
    issues = validate_benchmark_cases._validate_node(export, schema, schema, "<root>")
    first_issue = issues[0] if issues else None
    require(not issues, f"{path}: schema violation: {first_issue}")


def find_prohibited_keys(value: Any, path: str = "<root>") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.lower().replace("-", "_")
            if normalized in PROHIBITED_AGREEMENT_KEYS:
                hits.append(f"{path}.{key}")
            hits.extend(find_prohibited_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(find_prohibited_keys(child, f"{path}[{index}]"))
    return hits


def validate_completed_export(path: Path) -> None:
    export = load_json(path)
    validate_schema(export, path)
    require(export["schema_version"] == "0.1", "schema version mismatch")
    require(export["export_kind"] == "completed_human_review_export", "export kind mismatch")
    require(export["export_status"] == "completed_human_review", "export status mismatch")
    require(export["review_pass"] == "first_pass_blinded_pair_review", "review pass mismatch")

    prohibited = find_prohibited_keys(export)
    require(not prohibited, f"agreement/adjudication/statistical fields are not allowed in single export: {prohibited[:3]}")

    reviewer = export["reviewer"]
    reviewer_id = reviewer["reviewer_id"]
    require(reviewer["reviewer_kind"] == "real_human", "reviewer kind must be real_human")
    require(reviewer["codex_assisted"] is False, "Codex-assisted export cannot count as human review")
    require(reviewer["counts_as_human_review"] is True, "completed export must count as human review")
    require(
        not any(pattern.search(reviewer_id) for pattern in BLOCKED_REVIEWER_ID_PATTERNS),
        f"reviewer_id is blocked or placeholder-like: {reviewer_id}",
    )

    claim_boundary = export["claim_boundary"]
    require(claim_boundary["completed_single_human_review_only"] is True, "single-review boundary must be true")
    for key in (
        "reviewer_agreement_claimed",
        "adjudication_claimed",
        "completed_statistics_claimed",
        "prevalence_claim",
        "paper_grade_completion_claimed",
    ):
        require(claim_boundary[key] is False, f"{key} must be false")

    template_package_path = repo_path(export["input_refs"]["review_export_templates_ref"])
    bundle_path = repo_path(export["input_refs"]["blinded_packet_bundle_ref"])
    require(template_package_path is not None and template_package_path.is_file(), "missing review templates package")
    require(bundle_path is not None and bundle_path.is_file(), "missing blinded bundle")
    validate_gate5_review_export_templates.validate_package(template_package_path)

    export_lock = export["export_lock"]
    require(
        export_lock["template_package_sha256"] == build_gate5_review_packet_index.sha256_file(template_package_path),
        "template package hash mismatch",
    )
    require(
        export_lock["blinded_packet_bundle_sha256"] == build_gate5_review_packet_index.sha256_file(bundle_path),
        "blinded bundle hash mismatch",
    )

    package = load_json(template_package_path)
    matching_templates = [
        template
        for template in package["templates"]
        if template["export_id"] == export_lock["template_export_id"]
    ]
    require(len(matching_templates) == 1, "template_export_id must identify one template")
    template = matching_templates[0]
    expected_items = template["review_items"]
    observed_items = export["review_items"]
    require(len(observed_items) == len(expected_items), "completed export must cover every assigned review item")
    require(
        [item["review_item_id"] for item in observed_items] == [item["review_item_id"] for item in expected_items],
        "review item order or coverage mismatch",
    )
    seen_units: set[str] = set()
    for observed, expected in zip(observed_items, expected_items, strict=True):
        for key in ("review_item_id", "packet_id", "unit_id", "unit_type"):
            require(observed[key] == expected[key], f"{observed['review_item_id']}: {key} mismatch")
        require(observed["unit_id"] not in seen_units, f"duplicate unit id {observed['unit_id']}")
        seen_units.add(observed["unit_id"])
        response = observed["response"]
        require(response["response_status"] == "completed", f"{observed['review_item_id']}: response must be completed")
        if response["paper_claimable"] is True:
            require(response["exclusion_reason"] is None, f"{observed['review_item_id']}: claimable item cannot have exclusion reason")
        else:
            require(
                isinstance(response["exclusion_reason"], str) and response["exclusion_reason"].strip(),
                f"{observed['review_item_id']}: non-claimable item needs exclusion reason",
            )
        require(response["evidence_summary"].strip(), f"{observed['review_item_id']}: evidence summary required")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", nargs="?", type=Path, default=DEFAULT_EXPORT)
    args = parser.parse_args(argv)
    export_path = args.export if args.export.is_absolute() else REPO_ROOT / args.export
    validate_completed_export(export_path)
    print(f"validated Gate 5 completed human-review export: {export_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Gate 5 completed review export validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
