#!/usr/bin/env python3
"""Validate the Gate 5 manual review queue scaffold."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUEUE = REPO_ROOT / "benchmark" / "review" / "gate5-review-queue.json"
SCHEMA_PATH = REPO_ROOT / "schemas" / "gate5_review_queue.schema.json"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import build_gate5_review_queue  # noqa: E402
import validate_benchmark_cases  # noqa: E402
import validate_gate5_inclusion_table  # noqa: E402
import validate_paired_runtime_summary  # noqa: E402


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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def repo_path(ref: str | None) -> Path | None:
    if not isinstance(ref, str) or not ref:
        return None
    return REPO_ROOT / ref.split("#", 1)[0]


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


def validate_schema(queue: dict[str, Any], path: Path) -> None:
    schema = load_json(SCHEMA_PATH)
    issues = validate_benchmark_cases._validate_node(queue, schema, schema, "<root>")
    first_issue = issues[0] if issues else None
    require(not issues, f"{path}: schema violation: {first_issue}")


def validate_queue(path: Path) -> None:
    queue = load_json(path)
    validate_schema(queue, path)
    require(queue.get("schema_version") == "0.1", "schema version mismatch")
    require(queue.get("queue_id") == "gate5-review-queue", "queue id mismatch")
    require(queue.get("status") == "queued_not_reviewed", "status must be queued_not_reviewed")
    require(
        queue.get("analysis_script") == "tools/build_gate5_review_queue.py",
        "analysis script mismatch",
    )
    boundary = queue.get("boundary", "")
    require("manual review queue scaffold" in boundary, "boundary must identify queue scaffold")
    require("no completed human reviews" in boundary, "boundary must exclude completed reviews")
    require("reviewer agreement" in boundary, "boundary must mention reviewer agreement boundary")
    require("prevalence" in boundary, "boundary must exclude prevalence")

    prohibited = find_prohibited_keys(queue)
    require(not prohibited, f"prohibited reviewer/statistical result fields present: {prohibited[:3]}")
    placeholders = find_placeholders(queue)
    require(not placeholders, f"placeholder values present in queue: {placeholders[:3]}")

    claim_boundary = queue.get("claim_boundary", {})
    require(claim_boundary.get("review_queue_only") is True, "review_queue_only must be true")
    for key in (
        "completed_reviews_claimed",
        "reviewer_agreement_claimed",
        "adjudication_claimed",
        "completed_statistics_claimed",
        "prevalence_claim",
        "paper_grade_completion_claimed",
    ):
        require(claim_boundary.get(key) is False, f"claim boundary {key} must be false")

    input_refs = queue["input_refs"]
    inclusion_table_path = repo_path(input_refs["frozen_inclusion_table_ref"])
    paired_summary_path = repo_path(input_refs["paired_summary_ref"])
    adjudication_form_path = repo_path(input_refs["adjudication_form_ref"])
    require(inclusion_table_path is not None and inclusion_table_path.is_file(), "missing inclusion table")
    require(paired_summary_path is not None and paired_summary_path.is_file(), "missing paired summary")
    require(adjudication_form_path is not None and adjudication_form_path.is_file(), "missing adjudication form")
    validate_gate5_inclusion_table.validate_table(inclusion_table_path)
    validate_paired_runtime_summary.validate_summary(paired_summary_path)

    recomputed = build_gate5_review_queue.build_queue(
        inclusion_table_path,
        paired_summary_path,
        adjudication_form_path,
    )
    require(queue == recomputed, "Gate 5 manual review queue is stale")

    inclusion_table = load_json(inclusion_table_path)
    source_manifest_path = repo_path(inclusion_table["source_manifest_ref"])
    require(source_manifest_path is not None and source_manifest_path.is_file(), "missing source manifest")
    source_manifest = validate_benchmark_cases.load_json(source_manifest_path)
    schema = validate_benchmark_cases.load_schema()
    manifest_issues = validate_benchmark_cases.validate_manifest(source_manifest, source_manifest_path, schema)
    first_manifest_issue = manifest_issues[0] if manifest_issues else None
    require(not manifest_issues, f"source manifest failed validation: {first_manifest_issue}")
    source_cases = {case["case_id"]: case for case in source_manifest["cases"]}

    paired_summary = load_json(paired_summary_path)
    paired_groups = {
        group["group_key"]: group
        for group in paired_summary.get("groups", [])
        if isinstance(group, dict) and group.get("group_key")
    }
    included_entries = [
        entry
        for entry in inclusion_table.get("entries", [])
        if entry.get("included_in_gate5_descriptive_rates") is True
    ]
    included_by_case_id = {entry["case_id"]: entry for entry in included_entries}

    sampling = queue["sampling_frame"]
    require(sampling["source_denominator"] == len(included_entries), "sampling denominator mismatch")
    require(sampling["selection_locked_before_review"] is True, "selection must be locked")

    items = queue.get("review_items", [])
    aggregate = queue["aggregate"]
    require(len(items) == len(included_entries), "queue must contain one item per included case")
    require(aggregate["included_case_count"] == len(included_entries), "included case count mismatch")
    require(aggregate["queued_item_count"] == len(items), "queued item count mismatch")
    require(
        aggregate["queued_item_count"]
        == aggregate["paired_summary_mapped_item_count"] + aggregate["paired_summary_unmapped_item_count"],
        "mapped/unmapped count mismatch",
    )
    require(
        aggregate["review_status_counts"] == {"queued_not_reviewed": len(items)},
        "review status counts must be queued-only",
    )

    seen_item_ids: set[str] = set()
    seen_case_ids: set[str] = set()
    mapped_count = 0
    unmapped_count = 0
    blinding_count = 0
    for index, item in enumerate(items):
        item_id = item["review_item_id"]
        case_id = item["case_id"]
        require(item_id not in seen_item_ids, f"duplicate review item {item_id}")
        require(case_id not in seen_case_ids, f"duplicate queued case {case_id}")
        seen_item_ids.add(item_id)
        seen_case_ids.add(case_id)
        require(item_id.startswith(f"gate5-review-{index + 1:03d}-"), f"{item_id}: item order mismatch")
        require(item["review_status"] == "queued_not_reviewed", f"{item_id}: bad review status")
        require(case_id in included_by_case_id, f"{item_id}: case not in inclusion table")
        require(case_id in source_cases, f"{item_id}: case not in source manifest")

        entry = included_by_case_id[case_id]
        source_case = source_cases[case_id]
        require(item["case_pointer"] == entry["case_pointer"], f"{item_id}: case pointer mismatch")
        require(item["skill_id"] == entry["skill_id"], f"{item_id}: skill mismatch")
        require(item["task_id"] == entry["task_id"], f"{item_id}: task mismatch")
        require(item["contract_id"] == entry["contract_id"], f"{item_id}: contract mismatch")
        require(item["runtime_profiles"] == entry["runtime_profiles"], f"{item_id}: runtime profile mismatch")

        refs = item["refs"]
        for ref_key, must_be_file in (
            ("prompt_ref", True),
            ("contract_ref", True),
            ("workspace_ref", False),
            ("adjudication_form_ref", True),
        ):
            ref_path = repo_path(refs.get(ref_key))
            require(ref_path is not None, f"{item_id}: missing {ref_key}")
            if must_be_file:
                require(ref_path.is_file(), f"{item_id}: missing file {refs.get(ref_key)}")
            else:
                require(ref_path.is_dir(), f"{item_id}: missing directory {refs.get(ref_key)}")
        expected_ref = refs.get("expected_output_ref")
        expected_path = repo_path(expected_ref)
        if expected_ref is not None:
            require(expected_path is not None and expected_path.is_file(), f"{item_id}: missing expected output")

        hashes = refs["hashes"]
        require(
            hashes["prompt_sha256"] == source_case["task_prompt"]["prompt_sha256"],
            f"{item_id}: prompt hash mismatch",
        )
        require(
            hashes["workspace_snapshot_sha256"] == source_case["workspace"]["workspace_snapshot_sha256"],
            f"{item_id}: workspace hash mismatch",
        )
        require(
            hashes["contract_sha256"] == build_gate5_review_queue.sha256_file(REPO_ROOT / refs["contract_ref"]),
            f"{item_id}: contract hash mismatch",
        )
        if expected_path is None:
            require(hashes["expected_output_sha256"] is None, f"{item_id}: unexpected expected-output hash")
        else:
            require(
                hashes["expected_output_sha256"] == build_gate5_review_queue.sha256_file(expected_path),
                f"{item_id}: expected-output hash mismatch",
            )

        paired = item["paired_summary"]
        source_refs = paired["source_comparison_refs"]
        source_hashes = hashes["source_comparison_sha256s"]
        require(len(source_refs) == len(source_hashes), f"{item_id}: source-comparison hash count mismatch")
        for ref, observed_hash in zip(source_refs, source_hashes, strict=True):
            comparison_path = repo_path(ref)
            require(comparison_path is not None and comparison_path.is_file(), f"{item_id}: missing comparison ref {ref}")
            require(
                observed_hash == build_gate5_review_queue.sha256_file(comparison_path),
                f"{item_id}: comparison hash mismatch for {ref}",
            )

        if paired["status"] == "matched_variant_id":
            mapped_count += 1
            group_key = paired["group_key"]
            require(group_key in paired_groups, f"{item_id}: paired group missing")
            require(paired["pair_count"] > 0, f"{item_id}: matched group needs pair count")
            require(source_refs, f"{item_id}: matched group needs source comparisons")
            require(item["review_target"] == "case_plus_paired_summary_packet", f"{item_id}: bad review target")
            require(
                item["agreement_scope"] == "requires_two_independent_human_reviews_before_agreement",
                f"{item_id}: bad agreement scope",
            )
            if len(paired["runtime_profiles"]) > 1:
                blinding_count += 1
                require(
                    item["runtime_profile_blinding"] == "eligible_for_first_pass_blinding",
                    f"{item_id}: should be blinding eligible",
                )
        else:
            unmapped_count += 1
            require(paired["group_key"] is None, f"{item_id}: unmatched item must not set group key")
            require(paired["pair_count"] == 0, f"{item_id}: unmatched item must not set pair count")
            require(not source_refs, f"{item_id}: unmatched item must not set source comparisons")
            require(
                item["review_target"] == "case_metadata_packet",
                f"{item_id}: unmatched item must be metadata packet",
            )
            require(
                item["agreement_scope"] == "metadata_only_until_paired_summary_mapping_exists",
                f"{item_id}: unmatched item has wrong agreement scope",
            )
            require(
                item["review_reasons"] == ["unmapped_case_metadata_denominator"],
                f"{item_id}: unmatched item has wrong reasons",
            )

        packet_checks = item["packet_checks"]
        require(packet_checks["publishable_packet_checked"] is False, f"{item_id}: packet check must be pending")
        require(packet_checks["trace_finding_refs_expanded"] is False, f"{item_id}: trace expansion must be pending")
        require(packet_checks["real_secrets_allowed"] is False, f"{item_id}: real secrets must not be allowed")
        require(packet_checks["synthetic_canary_policy_required"] is True, f"{item_id}: canary policy must be required")

    require(set(included_by_case_id) == seen_case_ids, "queued cases do not match inclusion table")
    require(aggregate["paired_summary_mapped_item_count"] == mapped_count, "mapped item count mismatch")
    require(aggregate["paired_summary_unmapped_item_count"] == unmapped_count, "unmapped item count mismatch")
    require(aggregate["blinding_eligible_item_count"] == blinding_count, "blinding count mismatch")

    markdown_path = path.with_suffix(".md")
    require(markdown_path.is_file(), "missing Gate 5 review queue Markdown")
    markdown = markdown_path.read_text(encoding="utf-8")
    require(boundary in markdown, "Markdown boundary is stale")
    require(
        f"Queued items: `{aggregate['queued_item_count']}`" in markdown,
        "Markdown queued item count is stale",
    )
    require("This artifact is a queue only." in markdown, "Markdown queue-only boundary missing")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    args = parser.parse_args(argv)
    queue_path = args.queue if args.queue.is_absolute() else REPO_ROOT / args.queue
    validate_queue(queue_path)
    print("validated Gate 5 manual review queue")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Gate 5 manual review queue validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
