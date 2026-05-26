#!/usr/bin/env python3
"""Validate the Gate 5 first-pass blinded review-packet bundle."""

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
DEFAULT_BUNDLE = REPO_ROOT / "benchmark" / "review" / "gate5-blinded-packet-bundle.json"
SCHEMA_PATH = REPO_ROOT / "schemas" / "gate5_blinded_packet_bundle.schema.json"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import build_gate5_blinded_packet_bundle  # noqa: E402
import build_gate5_review_packet_index  # noqa: E402
import validate_benchmark_cases  # noqa: E402
import validate_gate5_review_packet_index  # noqa: E402
import validate_gate5_review_queue  # noqa: E402


PROHIBITED_RESULT_KEYS = {
    "reviewer_id",
    "reviewer_ids",
    "review_timestamp_utc",
    "reviewer_ids_compared",
    "adjudicator_id",
    "adjudication_timestamp_utc",
    "initial_agreement",
    "percent_agreement",
    "cohens_kappa",
    "kappa",
    "wilson_interval",
    "wilson_intervals",
    "bootstrap_interval",
    "bootstrap_intervals",
    "confidence_interval",
    "confidence_intervals",
    "mcnemar",
    "mcnemar_test",
    "hypothesis_test",
    "hypothesis_tests",
    "p_value",
    "p_values",
    "resolved_finding_kind",
    "resolved_drift_class",
    "resolved_severity",
    "resolved_paper_claimable",
}
PROHIBITED_PLACEHOLDERS = {"TBD", "TODO", "PLACEHOLDER"}
LOCAL_PATH_PATTERNS = [
    re.compile(pattern)
    for pattern in (
        "/" + r"Users/[^/\s\"']+",
        "/" + "private/" + r"var/folders/[^\s\"']+",
        "/" + "var/" + r"folders/[^\s\"']+",
    )
]
SECRET_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"(api[_-]?key|secret|token|cookie|authorization)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}",
        r"bearer\s+[A-Za-z0-9_\-\.]{20,}",
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
    validate_gate5_review_packet_index.require_recorded_git_identity(lock)


def normalize_git_identity(value: dict[str, Any], lock_key: str) -> dict[str, Any]:
    return validate_gate5_review_packet_index.normalize_git_identity(value, lock_key)


def validate_schema(bundle: dict[str, Any], path: Path) -> None:
    schema = load_json(SCHEMA_PATH)
    issues = validate_benchmark_cases._validate_node(bundle, schema, schema, "<root>")
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


def find_placeholders(value: Any, path: str = "<root>") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            hits.extend(find_placeholders(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(find_placeholders(child, f"{path}[{index}]"))
    elif isinstance(value, str) and value.strip() in PROHIBITED_PLACEHOLDERS:
        hits.append(path)
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


def assert_hidden_values_absent(container: Any, prohibited_values: list[str], label: str) -> None:
    text = json.dumps(container, sort_keys=True)
    leaks = [
        value
        for value in prohibited_values
        if isinstance(value, str) and value and value in text
    ]
    require(not leaks, f"{label}: blinded content leaked hidden value(s): {leaks[:3]}")


def validate_packet_pair(
    bundle_packet: dict[str, Any],
    index_packet: dict[str, Any],
) -> None:
    packet_id = index_packet["packet_id"]
    for key in (
        "packet_id",
        "review_item_id",
        "source_queue_pointer",
        "case_id",
        "variant_id",
        "sample_batch_id",
        "category",
        "source_mix_label",
        "evidence_stage",
        "blocked_reason",
        "runtime_profile_blinding",
        "agreement_scope",
    ):
        require(bundle_packet[key] == index_packet[key], f"{packet_id}: {key} mismatch")
    require(bundle_packet["base_refs"] == index_packet["base_refs"], f"{packet_id}: base refs mismatch")

    checks = bundle_packet["packet_checks"]
    for key in (
        "raw_trace_content_included",
        "local_path_content_included",
        "source_paths_in_review_packet",
        "runtime_evidence_paths_in_review_packet",
        "runtime_profile_labels_included",
        "source_run_ids_included",
        "machine_classification_included",
        "completed_review_included",
        "reviewer_fields_included",
    ):
        require(checks[key] is False, f"{packet_id}: {key} must be false")

    exported = index_packet["packet_status"] == "indexed_pending_sanitized_packet_export"
    require(checks["blinded_packet_exported"] is exported, f"{packet_id}: exported flag mismatch")
    if not exported:
        require(bundle_packet["bundle_status"] == "blocked_metadata_only_unmapped", f"{packet_id}: wrong blocked status")
        require(bundle_packet["review_mode"] == "metadata_only_unmapped_blocker", f"{packet_id}: wrong blocked review mode")
        require(not bundle_packet["blinded_evidence"]["comparison_refs"], f"{packet_id}: blocked packet has comparisons")
        require(not bundle_packet["blinded_evidence"]["runtime_slots"], f"{packet_id}: blocked packet has runtime slots")
        require(not bundle_packet["pair_review_units"], f"{packet_id}: blocked packet has pair units")
        require(not bundle_packet["finding_review_units"], f"{packet_id}: blocked packet has finding units")
        return

    require(bundle_packet["bundle_status"] == "blinded_first_pass_ready", f"{packet_id}: wrong exported status")
    require(bundle_packet["review_mode"] == "first_pass_blinded_pair_review", f"{packet_id}: wrong exported review mode")
    require(bundle_packet["blocked_reason"] is None, f"{packet_id}: exported packet cannot be blocked")

    comparison_refs = bundle_packet["blinded_evidence"]["comparison_refs"]
    runtime_slots = bundle_packet["blinded_evidence"]["runtime_slots"]
    pair_units = bundle_packet["pair_review_units"]
    finding_units = bundle_packet["finding_review_units"]
    require(len(comparison_refs) == len(index_packet["comparison_refs"]), f"{packet_id}: comparison count mismatch")
    require(len(runtime_slots) == len(index_packet["run_refs"]), f"{packet_id}: runtime slot count mismatch")
    require(len(pair_units) == len(index_packet["pair_refs"]), f"{packet_id}: pair unit count mismatch")
    require(len(finding_units) == len(index_packet["finding_refs"]), f"{packet_id}: finding unit count mismatch")

    comparison_id_by_ref: dict[str, str] = {}
    for number, (bundle_ref, index_ref) in enumerate(zip(comparison_refs, index_packet["comparison_refs"], strict=True)):
        expected_id = f"{packet_id}.comparison_ref.{number}"
        comparison_id_by_ref[index_ref["comparison_ref"]] = expected_id
        require(bundle_ref["comparison_ref_id"] == expected_id, f"{packet_id}: comparison ref id mismatch")
        require(bundle_ref["source_ref_hidden"] is True, f"{packet_id}: comparison source ref must be hidden")
        require(bundle_ref["comparison_sha256"] == index_ref["comparison_sha256"], f"{packet_id}: comparison hash mismatch")
        require(bundle_ref["run_count"] == index_ref["run_count"], f"{packet_id}: comparison run count mismatch")
        require(bundle_ref["pair_count"] == index_ref["pair_count"], f"{packet_id}: comparison pair count mismatch")

    slot_id_by_run_id: dict[str, str] = {}
    for number, (slot, run_ref) in enumerate(zip(runtime_slots, index_packet["run_refs"], strict=True)):
        expected_slot_id = f"{packet_id}.runtime_slot.{number}"
        slot_id_by_run_id[run_ref["run_id"]] = expected_slot_id
        require(slot["slot_id"] == expected_slot_id, f"{packet_id}: slot id mismatch")
        require(slot["slot_label"] == build_gate5_blinded_packet_bundle.slot_label(number), f"{packet_id}: slot label mismatch")
        require(slot["run_pointer"] == run_ref["run_pointer"], f"{packet_id}: run pointer mismatch")
        require(slot["repeat_id"] == run_ref["repeat_id"], f"{packet_id}: repeat id mismatch")
        require(slot["source_run_id_hidden"] is True, f"{packet_id}: run id must be hidden")
        require(slot["runtime_profile_hidden"] is True, f"{packet_id}: runtime profile must be hidden")
        require(slot["source_ref_hidden"] is True, f"{packet_id}: source refs must be hidden")
        require(slot["finding_artifact_ref_id"] == f"{packet_id}.finding_artifact.{number}", f"{packet_id}: finding artifact id mismatch")
        require(slot["finding_sha256"] == run_ref["finding_sha256"], f"{packet_id}: finding hash mismatch")
        require(slot["trace_artifact_ref_id"] == f"{packet_id}.trace_artifact.{number}", f"{packet_id}: trace artifact id mismatch")
        require(slot["trace_sha256"] == run_ref["trace_sha256"], f"{packet_id}: trace hash mismatch")
        require(slot["trace_valid"] == run_ref["trace_valid"], f"{packet_id}: trace valid mismatch")
        require(slot["trace_event_count"] == run_ref["trace_event_count"], f"{packet_id}: trace count mismatch")
        require(slot["finding_count"] == run_ref["finding_count"], f"{packet_id}: finding count mismatch")

    for number, (unit, pair_ref) in enumerate(zip(pair_units, index_packet["pair_refs"], strict=True)):
        require(unit["unit_id"] == f"{packet_id}.pair_unit.{number}", f"{packet_id}: pair unit id mismatch")
        require(unit["unit_type"] == "runtime_pair_comparison", f"{packet_id}: pair unit type mismatch")
        require(unit["unit_status"] == "pending_manual_review", f"{packet_id}: pair unit status mismatch")
        require(unit["claim_boundary"] == "not_human_reviewed", f"{packet_id}: pair unit boundary mismatch")
        require(unit["comparison_ref_id"] == comparison_id_by_ref[pair_ref["comparison_ref"]], f"{packet_id}: pair comparison id mismatch")
        require(unit["pair_pointer"] == pair_ref["pair_pointer"], f"{packet_id}: pair pointer mismatch")
        require(unit["left_slot_id"] == slot_id_by_run_id[pair_ref["left_run_id"]], f"{packet_id}: left slot mismatch")
        require(unit["right_slot_id"] == slot_id_by_run_id[pair_ref["right_run_id"]], f"{packet_id}: right slot mismatch")
        require(unit["runtime_labels_hidden"] is True, f"{packet_id}: pair runtime labels must be hidden")
        require(unit["machine_classification_hidden"] is True, f"{packet_id}: pair classification must be hidden")
        require(unit["source_ref_hidden"] is True, f"{packet_id}: pair source refs must be hidden")
        require(unit["completed_review_included"] is False, f"{packet_id}: pair unit must not include review")

    for number, unit in enumerate(finding_units):
        require(unit["unit_id"] == f"{packet_id}.finding_unit.{number}", f"{packet_id}: finding unit id mismatch")
        require(unit["unit_type"] == "contract_finding", f"{packet_id}: finding unit type mismatch")
        require(unit["unit_status"] == "pending_manual_review", f"{packet_id}: finding unit status mismatch")
        require(unit["claim_boundary"] == "not_human_reviewed", f"{packet_id}: finding unit boundary mismatch")
        require(unit["runtime_labels_hidden"] is True, f"{packet_id}: finding runtime labels must be hidden")
        require(unit["source_ref_hidden"] is True, f"{packet_id}: finding source refs must be hidden")
        require(unit["completed_review_included"] is False, f"{packet_id}: finding unit must not include review")

    hidden_values: list[str] = []
    for comparison_ref in index_packet["comparison_refs"]:
        hidden_values.append(comparison_ref["comparison_ref"])
    for run_ref in index_packet["run_refs"]:
        hidden_values.extend(
            [
                run_ref["run_id"],
                run_ref["runtime_profile"],
                run_ref["finding_ref"],
                run_ref["trace_ref"],
            ]
        )
    for pair_ref in index_packet["pair_refs"]:
        hidden_values.extend(
            [
                pair_ref["left_run_id"],
                pair_ref["right_run_id"],
                pair_ref["classification_claim"],
            ]
        )
    assert_hidden_values_absent(
        {
            "blinded_evidence": bundle_packet["blinded_evidence"],
            "pair_review_units": bundle_packet["pair_review_units"],
            "finding_review_units": bundle_packet["finding_review_units"],
        },
        hidden_values,
        packet_id,
    )


def validate_bundle(path: Path) -> None:
    bundle = load_json(path)
    validate_schema(bundle, path)
    require(bundle.get("schema_version") == "0.1", "schema version mismatch")
    require(bundle.get("bundle_id") == "gate5-blinded-packet-bundle", "bundle id mismatch")
    require(
        bundle.get("status") == "blinded_packet_bundle_ready_no_completed_reviews",
        "status must remain no-completed-reviews",
    )
    require(
        bundle.get("analysis_script") == "tools/build_gate5_blinded_packet_bundle.py",
        "analysis script mismatch",
    )
    boundary = bundle.get("boundary", "")
    require("first-pass blinded packet bundle" in boundary, "boundary must identify blinded bundle")
    require("opaque evidence identifiers" in boundary, "boundary must describe opaque refs")
    require("raw trace content" in boundary, "boundary must exclude raw trace content")
    require("completed human reviews" in boundary, "boundary must exclude completed reviews")
    require("reviewer agreement" in boundary, "boundary must exclude agreement")
    require("prevalence" in boundary, "boundary must exclude prevalence")

    prohibited = find_prohibited_keys(bundle)
    require(not prohibited, f"prohibited reviewer/statistical result fields present: {prohibited[:3]}")
    placeholders = find_placeholders(bundle)
    require(not placeholders, f"placeholder values present in blinded bundle: {placeholders[:3]}")

    markdown_path = path.with_suffix(".md")
    require(markdown_path.is_file(), "missing blinded-bundle Markdown")
    scan_findings = scan_text_artifact(path) + scan_text_artifact(markdown_path)
    require(not scan_findings, f"blinded-bundle artifact hygiene failed: {scan_findings[:3]}")
    require(
        "This artifact is a blinded packet bundle only." in markdown_path.read_text(encoding="utf-8"),
        "Markdown must state blinded-bundle-only boundary",
    )

    claim_boundary = bundle.get("claim_boundary", {})
    require(claim_boundary.get("blinded_packet_bundle_only") is True, "bundle-only boundary must be true")
    require(claim_boundary.get("first_pass_runtime_labels_blinded") is True, "first-pass labels must be blinded")
    require(claim_boundary.get("raw_trace_content_included") is False, "raw trace content must be excluded")
    require(
        claim_boundary.get("runtime_evidence_paths_in_review_packets") is False,
        "runtime evidence paths must be excluded",
    )
    for key in (
        "completed_reviews_claimed",
        "reviewer_agreement_claimed",
        "adjudication_claimed",
        "completed_statistics_claimed",
        "prevalence_claim",
        "paper_grade_completion_claimed",
    ):
        require(claim_boundary.get(key) is False, f"claim boundary {key} must be false")

    input_refs = bundle["input_refs"]
    index_path = repo_path(input_refs["review_packet_index_ref"])
    queue_path = repo_path(input_refs["review_queue_ref"])
    adjudication_form_path = repo_path(input_refs["adjudication_form_ref"])
    require(index_path is not None and index_path.is_file(), "missing review-packet index")
    require(queue_path is not None and queue_path.is_file(), "missing review queue")
    require(adjudication_form_path is not None and adjudication_form_path.is_file(), "missing adjudication form")
    validate_gate5_review_packet_index.validate_index(index_path)
    validate_gate5_review_queue.validate_queue(queue_path)

    bundle_lock = bundle["bundle_lock"]
    require_recorded_git_identity(bundle_lock)
    input_hashes = bundle_lock["input_hashes"]
    for key, artifact_path in (
        ("review_packet_index_sha256", index_path),
        ("review_queue_sha256", queue_path),
        ("adjudication_form_sha256", adjudication_form_path),
    ):
        require(
            input_hashes[key] == build_gate5_review_packet_index.sha256_file(artifact_path),
            f"input hash mismatch for {key}",
        )

    recomputed = build_gate5_blinded_packet_bundle.build_bundle(index_path)
    require(
        normalize_git_identity(bundle, "bundle_lock") == normalize_git_identity(recomputed, "bundle_lock"),
        "Gate 5 blinded packet bundle is stale",
    )

    packet_index = load_json(index_path)
    index_packets = packet_index.get("packets", [])
    aggregate = bundle["aggregate"]
    packets = bundle.get("packets", [])
    require(len(packets) == len(index_packets), "bundle must contain one record per index packet")
    require(aggregate["source_packet_count"] == len(index_packets), "source packet count mismatch")
    require(aggregate["source_packet_count"] == aggregate["exported_packet_count"] + aggregate["blocked_packet_count"], "exported/blocked count mismatch")
    require(aggregate["exported_packet_count"] == packet_index["aggregate"]["indexed_packet_count"], "export count mismatch")
    require(aggregate["blocked_packet_count"] == packet_index["aggregate"]["blocked_packet_count"], "blocked count mismatch")
    require(aggregate["opaque_comparison_ref_count"] == packet_index["aggregate"]["comparison_ref_count"], "comparison ref count mismatch")
    require(aggregate["opaque_finding_artifact_ref_count"] == packet_index["aggregate"]["run_ref_count"], "finding artifact count mismatch")
    require(aggregate["opaque_trace_artifact_ref_count"] == packet_index["aggregate"]["trace_ref_count"], "trace artifact count mismatch")
    require(aggregate["runtime_slot_count"] == packet_index["aggregate"]["run_ref_count"], "runtime slot count mismatch")
    require(aggregate["pair_review_unit_count"] == packet_index["aggregate"]["pair_review_unit_count"], "pair review unit count mismatch")
    require(aggregate["finding_review_unit_count"] == packet_index["aggregate"]["finding_review_unit_count"], "finding review unit count mismatch")
    require(aggregate["raw_trace_payload_count"] == 0, "raw trace payload count must be zero")
    require(aggregate["completed_review_count"] == 0, "completed review count must be zero")
    require(aggregate["reviewer_identity_count"] == 0, "reviewer identity count must be zero")

    status_counts = Counter(packet["bundle_status"] for packet in packets)
    require(aggregate["packet_status_counts"] == dict(sorted(status_counts.items())), "status count mismatch")

    seen_packet_ids: set[str] = set()
    seen_review_item_ids: set[str] = set()
    for bundle_packet, index_packet in zip(packets, index_packets, strict=True):
        require(bundle_packet["packet_id"] not in seen_packet_ids, f"duplicate packet {bundle_packet['packet_id']}")
        require(bundle_packet["review_item_id"] not in seen_review_item_ids, f"duplicate item {bundle_packet['review_item_id']}")
        seen_packet_ids.add(bundle_packet["packet_id"])
        seen_review_item_ids.add(bundle_packet["review_item_id"])
        validate_packet_pair(bundle_packet, index_packet)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    args = parser.parse_args(argv)
    bundle_path = args.bundle if args.bundle.is_absolute() else REPO_ROOT / args.bundle
    validate_bundle(bundle_path)
    print(f"validated Gate 5 blinded packet bundle: {bundle_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Gate 5 blinded packet bundle validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
