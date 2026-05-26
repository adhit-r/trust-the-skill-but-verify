#!/usr/bin/env python3
"""Validate the frozen Gate 5 inclusion table."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TABLE = REPO_ROOT / "benchmark" / "manifests" / "gate5-paper-inclusion.json"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import build_gate5_inclusion_table  # noqa: E402
import validate_benchmark_cases  # noqa: E402
import validate_paired_runtime_summary  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def repo_path(ref: str | None) -> Path | None:
    if not isinstance(ref, str) or not ref:
        return None
    path_part = ref.split("#", 1)[0]
    return REPO_ROOT / path_part


def validate_table(path: Path) -> None:
    table = load_json(path)
    require(table.get("schema_version") == "0.1", "schema version mismatch")
    require(table.get("table_id") == "gate5-paper-inclusion", "table id mismatch")
    require(table.get("status") == "frozen_for_descriptive_rates_only", "status mismatch")
    boundary = table.get("boundary", "")
    require("descriptive rates only" in boundary, "boundary must limit table to descriptive rates")
    require("not completed statistics" in boundary, "boundary must exclude completed statistics")
    require("not reviewer agreement" in boundary, "boundary must exclude reviewer agreement")
    require("not prevalence" in boundary, "boundary must exclude prevalence")

    claim_boundary = table.get("claim_boundary", {})
    require(claim_boundary.get("descriptive_rates_only") is True, "descriptive_rates_only must be true")
    for key in (
        "completed_statistics_claimed",
        "reviewer_agreement_claimed",
        "prevalence_claim",
        "source_mix_completion_claimed",
        "paper_grade_completion_claimed",
    ):
        require(claim_boundary.get(key) is False, f"claim boundary {key} must be false")

    source_manifest_path = repo_path(table.get("source_manifest_ref"))
    paired_summary_path = repo_path(table.get("paired_runtime_summary_ref"))
    require(source_manifest_path is not None and source_manifest_path.is_file(), "source manifest missing")
    require(paired_summary_path is not None and paired_summary_path.is_file(), "paired summary missing")

    manifest = validate_benchmark_cases.load_json(source_manifest_path)
    schema = validate_benchmark_cases.load_schema()
    manifest_issues = validate_benchmark_cases.validate_manifest(manifest, source_manifest_path, schema)
    first_issue = manifest_issues[0] if manifest_issues else None
    require(not manifest_issues, f"source manifest failed validation: {first_issue}")
    validate_paired_runtime_summary.validate_summary(paired_summary_path)

    recomputed = build_gate5_inclusion_table.build_table(source_manifest_path, paired_summary_path)
    require(table == recomputed, "Gate 5 inclusion table is stale")

    entries = table.get("entries", [])
    require(table.get("declared_case_count") == len(entries), "declared case count mismatch")
    require(len(entries) == len(manifest.get("cases", [])), "entry count must match benchmark cases")
    seen_case_ids: set[str] = set()
    paired_summary = load_json(paired_summary_path)
    group_keys = {
        group["group_key"]
        for group in paired_summary.get("groups", [])
        if isinstance(group, dict) and group.get("group_key")
    }

    for index, entry in enumerate(entries):
        case_id = entry.get("case_id")
        require(isinstance(case_id, str) and case_id, f"entry {index}: missing case_id")
        require(case_id not in seen_case_ids, f"duplicate case_id {case_id}")
        seen_case_ids.add(case_id)

        source_case = manifest["cases"][index]
        require(case_id == source_case["case_id"], f"{case_id}: case order mismatch")
        require(entry.get("case_pointer") == f"/cases/{index}", f"{case_id}: case pointer mismatch")
        require(entry.get("skill_id") == source_case["provenance"]["skill_id"], f"{case_id}: skill mismatch")
        require(entry.get("task_id") == source_case["provenance"]["task_id"], f"{case_id}: task mismatch")
        require(entry.get("contract_id") == source_case["contract"]["contract_id"], f"{case_id}: contract mismatch")
        require(entry.get("category") == source_case["category"], f"{case_id}: category mismatch")
        require(
            entry.get("source_mix_label") == source_case["provenance"]["source_mix"]["label"],
            f"{case_id}: source-mix mismatch",
        )
        require(entry.get("prompt_ref") == source_case["task_prompt"]["prompt_ref"], f"{case_id}: prompt mismatch")
        require(entry.get("contract_ref") == source_case["contract"]["contract_ref"], f"{case_id}: contract ref mismatch")
        require(entry.get("workspace_ref") == source_case["workspace"]["workspace_ref"], f"{case_id}: workspace ref mismatch")

        for ref_key, must_be_file in (
            ("prompt_ref", True),
            ("contract_ref", True),
            ("workspace_ref", False),
        ):
            ref_path = repo_path(entry.get(ref_key))
            require(ref_path is not None, f"{case_id}: {ref_key} missing")
            if must_be_file:
                require(ref_path.is_file(), f"{case_id}: {ref_key} does not exist: {entry.get(ref_key)}")
            else:
                require(ref_path.is_dir(), f"{case_id}: {ref_key} does not exist: {entry.get(ref_key)}")
        expected_ref = entry.get("expected_output_ref")
        if expected_ref is not None:
            expected_path = repo_path(expected_ref)
            require(expected_path is not None and expected_path.is_file(), f"{case_id}: expected output ref missing")

        included = entry.get("included_in_gate5_descriptive_rates")
        if included is True:
            require(entry.get("exclusion_reason") is None, f"{case_id}: included case must not have exclusion reason")
        else:
            require(isinstance(entry.get("exclusion_reason"), str), f"{case_id}: excluded case needs reason")

        group_key = entry.get("paired_summary_group_key")
        if entry.get("paired_summary_status") == "matched_variant_id":
            require(group_key in group_keys, f"{case_id}: paired summary group missing")
        else:
            require(group_key is None, f"{case_id}: unmatched case must not set group key")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table", type=Path, default=DEFAULT_TABLE)
    args = parser.parse_args(argv)
    table_path = args.table if args.table.is_absolute() else REPO_ROOT / args.table
    validate_table(table_path)
    print("validated Gate 5 inclusion table")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Gate 5 inclusion table validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
