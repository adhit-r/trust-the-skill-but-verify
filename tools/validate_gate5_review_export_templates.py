#!/usr/bin/env python3
"""Validate Gate 5 blank human-review export templates."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = REPO_ROOT / "benchmark" / "review" / "gate5-review-export-templates.json"
SCHEMA_PATH = REPO_ROOT / "schemas" / "gate5_review_export_templates.schema.json"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import build_gate5_review_export_templates  # noqa: E402
import build_gate5_review_packet_index  # noqa: E402
import validate_benchmark_cases  # noqa: E402
import validate_gate5_blinded_packet_bundle  # noqa: E402


PROHIBITED_RESULT_KEYS = validate_gate5_blinded_packet_bundle.PROHIBITED_RESULT_KEYS
LOCAL_PATH_PATTERNS = validate_gate5_blinded_packet_bundle.LOCAL_PATH_PATTERNS
SECRET_PATTERNS = validate_gate5_blinded_packet_bundle.SECRET_PATTERNS
RUNTIME_LEAK_PATTERNS = [
    re.compile(pattern)
    for pattern in (
        r"\bRP[1-6]\b",
        r"\brp[1-6]-[0-9a-f]{8,}\b",
        r"_rp[1-6]",
        r"results/(raw|mvp|planned-inclusion|fixtures)/",
        r"trace\.jsonl",
        r"contract_findings",
        r"runtime_drift_candidate",
        r"no_pairwise_disagreement",
    )
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def repo_path(ref: str | None) -> Path | None:
    if not isinstance(ref, str) or not ref:
        return None
    return REPO_ROOT / ref.split("#", 1)[0]


def git_rev_parse(rev: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", rev],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def require_recorded_git_identity(lock: dict[str, Any]) -> None:
    validate_gate5_blinded_packet_bundle.require_recorded_git_identity(lock)


def normalize_git_identity(value: dict[str, Any], lock_key: str) -> dict[str, Any]:
    return validate_gate5_blinded_packet_bundle.normalize_git_identity(value, lock_key)


def validate_schema(package: dict[str, Any], path: Path) -> None:
    schema = load_json(SCHEMA_PATH)
    issues = validate_benchmark_cases._validate_node(package, schema, schema, "<root>")
    first_issue = issues[0] if issues else None
    require(not issues, f"{path}: schema violation: {first_issue}")


def find_prohibited_keys(value: Any, path: str = "<root>") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = key.lower().replace("-", "_")
            if normalized_key in PROHIBITED_RESULT_KEYS:
                hits.append(f"{path}.{key}")
            hits.extend(find_prohibited_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(find_prohibited_keys(child, f"{path}[{index}]"))
    return hits


def scan_text_artifact(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8")
    for line_no, line in enumerate(text.splitlines(), start=1):
        if any(pattern.search(line) for pattern in LOCAL_PATH_PATTERNS):
            findings.append(f"{path.relative_to(REPO_ROOT)}:{line_no}: local path")
        if any(pattern.search(line) for pattern in SECRET_PATTERNS):
            findings.append(f"{path.relative_to(REPO_ROOT)}:{line_no}: secret-like token")
    return findings


def assert_no_runtime_leaks(value: Any, path: str = "<root>") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            assert_no_runtime_leaks(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_no_runtime_leaks(child, f"{path}[{index}]")
    elif isinstance(value, str):
        for pattern in RUNTIME_LEAK_PATTERNS:
            require(not pattern.search(value), f"{path}: runtime/source leak {value!r}")


def validate_package(path: Path) -> None:
    package = load_json(path)
    validate_schema(package, path)
    require(package["schema_version"] == "0.1", "schema version mismatch")
    require(package["template_package_id"] == "gate5-review-export-templates", "template package id mismatch")
    require(package["status"] == "review_export_templates_ready_no_completed_reviews", "status mismatch")
    require(package["analysis_script"] == "tools/build_gate5_review_export_templates.py", "analysis script mismatch")
    boundary = package["boundary"]
    require("blank first-pass human-review export templates" in boundary, "boundary must identify blank templates")
    require("not completed reviews" in boundary, "boundary must exclude completed review")
    require("no human reviewer identity" in boundary, "boundary must exclude reviewer identity")
    require("agreement metric" in boundary, "boundary must exclude agreement")
    require("prevalence" in boundary, "boundary must exclude prevalence")

    prohibited = find_prohibited_keys(package)
    require(not prohibited, f"prohibited completed-result keys present: {prohibited[:3]}")
    assert_no_runtime_leaks(package)

    markdown_path = path.with_suffix(".md")
    require(markdown_path.is_file(), "missing review-template Markdown")
    scan_findings = scan_text_artifact(path) + scan_text_artifact(markdown_path)
    require(not scan_findings, f"review-template artifact hygiene failed: {scan_findings[:3]}")
    require(
        "This artifact is a review-template package only." in markdown_path.read_text(encoding="utf-8"),
        "Markdown must state template-only boundary",
    )

    claim_boundary = package["claim_boundary"]
    require(claim_boundary["review_export_templates_only"] is True, "template-only boundary must be true")
    for key in (
        "completed_human_reviews_claimed",
        "human_reviewer_identity_claimed",
        "reviewer_agreement_claimed",
        "adjudication_claimed",
        "completed_statistics_claimed",
        "prevalence_claim",
        "paper_grade_completion_claimed",
        "codex_assisted_review_counted_as_human",
    ):
        require(claim_boundary[key] is False, f"{key} must be false")

    input_refs = package["input_refs"]
    bundle_path = repo_path(input_refs["blinded_packet_bundle_ref"])
    adjudication_form_path = repo_path(input_refs["adjudication_form_ref"])
    require(bundle_path is not None and bundle_path.is_file(), "missing blinded bundle")
    require(adjudication_form_path is not None and adjudication_form_path.is_file(), "missing adjudication form")
    validate_gate5_blinded_packet_bundle.validate_bundle(bundle_path)

    package_lock = package["package_lock"]
    require_recorded_git_identity(package_lock)
    input_hashes = package_lock["input_hashes"]
    for key, artifact_path in (
        ("blinded_packet_bundle_sha256", bundle_path),
        ("adjudication_form_sha256", adjudication_form_path),
    ):
        require(
            input_hashes[key] == build_gate5_review_packet_index.sha256_file(artifact_path),
            f"input hash mismatch for {key}",
        )

    recomputed = build_gate5_review_export_templates.build_templates(bundle_path)
    require(
        normalize_git_identity(package, "package_lock") == normalize_git_identity(recomputed, "package_lock"),
        "Gate 5 review export templates are stale",
    )

    bundle = load_json(bundle_path)
    exported_packets = [
        packet
        for packet in bundle["packets"]
        if packet["bundle_status"] == "blinded_first_pass_ready"
    ]
    blocked_packets = [
        packet
        for packet in bundle["packets"]
        if packet["bundle_status"] == "blocked_metadata_only_unmapped"
    ]
    expected_unit_ids = [
        unit["unit_id"]
        for packet in exported_packets
        for unit in packet["pair_review_units"]
    ]
    packet_by_id = {packet["packet_id"]: packet for packet in exported_packets}
    blocked_by_id = {packet["packet_id"]: packet for packet in blocked_packets}

    aggregate = package["aggregate"]
    templates = package["templates"]
    require(aggregate["template_count"] == len(templates), "template count mismatch")
    require(aggregate["source_packet_count"] == bundle["aggregate"]["source_packet_count"], "source packet count mismatch")
    require(aggregate["assigned_packet_count_per_template"] == len(exported_packets), "assigned packet count mismatch")
    require(aggregate["blocked_packet_count"] == len(blocked_packets), "blocked packet count mismatch")
    require(aggregate["assigned_pair_review_unit_count_per_template"] == len(expected_unit_ids), "pair unit count mismatch")
    require(aggregate["assigned_finding_review_unit_count_per_template"] == bundle["aggregate"]["finding_review_unit_count"], "finding unit count mismatch")
    for key in (
        "completed_review_export_count",
        "completed_pair_review_unit_count",
        "human_reviewer_identity_count",
        "agreement_metric_count",
        "adjudication_record_count",
    ):
        require(aggregate[key] == 0, f"{key} must be zero")
    status_counts = Counter(template["template_status"] for template in templates)
    require(aggregate["template_status_counts"] == dict(sorted(status_counts.items())), "template status count mismatch")

    seen_export_ids: set[str] = set()
    reviewer_slots: set[str] = set()
    for template in templates:
        export_id = template["export_id"]
        require(export_id not in seen_export_ids, f"duplicate export id {export_id}")
        seen_export_ids.add(export_id)
        assignment = template["assignment"]
        reviewer_slots.add(assignment["reviewer_slot"])
        require(assignment["reviewer_kind"] == "unassigned_human", f"{export_id}: reviewer kind mismatch")
        require(assignment["human_identity_claimed"] is False, f"{export_id}: human identity cannot be claimed")
        require(assignment["codex_assisted"] is False, f"{export_id}: codex assisted must be false")
        require(assignment["counts_as_human_review"] is False, f"{export_id}: template cannot count as human review")
        template_boundary = template["claim_boundary"]
        require(template_boundary["template_only"] is True, f"{export_id}: template-only boundary missing")
        require(template_boundary["completed_review_claimed"] is False, f"{export_id}: completed review claim present")
        require(template_boundary["agreement_claimed"] is False, f"{export_id}: agreement claim present")
        require(template_boundary["adjudication_claimed"] is False, f"{export_id}: adjudication claim present")
        review_items = template["review_items"]
        require(len(review_items) == len(expected_unit_ids), f"{export_id}: review item count mismatch")
        require([item["unit_id"] for item in review_items] == expected_unit_ids, f"{export_id}: unit order mismatch")
        seen_review_items: set[str] = set()
        for item in review_items:
            require(item["review_item_id"] not in seen_review_items, f"{export_id}: duplicate review item")
            seen_review_items.add(item["review_item_id"])
            packet = packet_by_id[item["packet_id"]]
            pair_unit = next(unit for unit in packet["pair_review_units"] if unit["unit_id"] == item["unit_id"])
            for key in ("case_id", "variant_id", "category", "source_mix_label", "evidence_stage"):
                require(item[key] == packet[key], f"{export_id}: {item['unit_id']}: {key} mismatch")
            require(item["unit_type"] == pair_unit["unit_type"], f"{export_id}: unit type mismatch")
            require(item["comparison_ref_id"] == pair_unit["comparison_ref_id"], f"{export_id}: comparison ref mismatch")
            require(item["pair_pointer"] == pair_unit["pair_pointer"], f"{export_id}: pair pointer mismatch")
            require(item["left_slot_id"] == pair_unit["left_slot_id"], f"{export_id}: left slot mismatch")
            require(item["right_slot_id"] == pair_unit["right_slot_id"], f"{export_id}: right slot mismatch")
            require(item["base_refs"] == packet["base_refs"], f"{export_id}: base refs mismatch")
            for hidden_key in (
                "runtime_labels_hidden",
                "source_run_ids_hidden",
                "machine_classification_hidden",
                "runtime_evidence_paths_hidden",
            ):
                require(item["blinding"][hidden_key] is True, f"{export_id}: {hidden_key} must be true")
            response = item["response"]
            require(response["response_status"] == "not_started", f"{export_id}: response status must be not_started")
            for response_key, response_value in response.items():
                if response_key != "response_status":
                    require(response_value is None, f"{export_id}: {item['unit_id']}: {response_key} must be null")
    require(reviewer_slots == {"reviewer_a", "reviewer_b"}, "expected reviewer_a and reviewer_b templates")

    blocked_records = package["blocked_packets"]
    require(len(blocked_records) == len(blocked_packets), "blocked packet count mismatch")
    for blocked_record in blocked_records:
        packet = blocked_by_id[blocked_record["packet_id"]]
        require(blocked_record["review_item_id"] == packet["review_item_id"], "blocked review item mismatch")
        require(blocked_record["case_id"] == packet["case_id"], "blocked case mismatch")
        require(blocked_record["blocked_reason"] == packet["blocked_reason"], "blocked reason mismatch")
        require(
            blocked_record["review_assignment_status"] == "not_assigned_metadata_only_unmapped",
            "blocked assignment status mismatch",
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    args = parser.parse_args(argv)
    package_path = args.package if args.package.is_absolute() else REPO_ROOT / args.package
    validate_package(package_path)
    print(f"validated Gate 5 review export templates: {package_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Gate 5 review export template validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
