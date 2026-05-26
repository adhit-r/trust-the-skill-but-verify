#!/usr/bin/env python3
"""Build the frozen Gate 5 inclusion table for descriptive rates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "benchmark" / "manifests" / "benchmark-cases-current.json"
DEFAULT_PAIRED_SUMMARY = REPO_ROOT / "results" / "derived" / "paired-runtime-summary.json"
DEFAULT_OUTPUT = REPO_ROOT / "benchmark" / "manifests" / "gate5-paper-inclusion.json"
FROZEN_DATE = "2026-05-26"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def build_table(
    manifest_path: Path = DEFAULT_MANIFEST,
    paired_summary_path: Path = DEFAULT_PAIRED_SUMMARY,
) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    paired_summary = load_json(paired_summary_path)
    groups_by_variant = {
        group["variant_id"]: group
        for group in paired_summary.get("groups", [])
        if isinstance(group, dict) and group.get("variant_id")
    }

    entries: list[dict[str, Any]] = []
    for index, case in enumerate(manifest.get("cases", [])):
        provenance = case["provenance"]
        execution = case["execution"]
        expected_output = case["expected_output"]
        group = groups_by_variant.get(case["case_id"])
        entries.append(
            {
                "case_id": case["case_id"],
                "case_pointer": f"/cases/{index}",
                "family_id": case["family_id"],
                "skill_id": provenance["skill_id"],
                "task_id": provenance["task_id"],
                "contract_id": case["contract"]["contract_id"],
                "category": case["category"],
                "case_status": case["case_status"],
                "source_mix_label": provenance["source_mix"]["label"],
                "evidence_stage": execution["evidence_stage"],
                "execution_level": execution["execution_level"],
                "runtime_profiles": execution["runtime_profiles"],
                "manifest_ref": f"{rel(manifest_path)}#/cases/{index}",
                "prompt_ref": case["task_prompt"]["prompt_ref"],
                "contract_ref": case["contract"]["contract_ref"],
                "workspace_ref": case["workspace"]["workspace_ref"],
                "expected_output_ref": expected_output.get("oracle_ref"),
                "included_in_gate5_descriptive_rates": True,
                "inclusion_scope": "current_benchmark_inventory_descriptive_rates",
                "exclusion_reason": None,
                "paired_summary_group_key": group["group_key"] if group is not None else None,
                "paired_summary_status": (
                    "matched_variant_id"
                    if group is not None
                    else "not_mapped_to_existing_paired_summary_group"
                ),
                "claim_boundary": "descriptive_denominator_only_not_statistics",
            }
        )

    return {
        "schema_version": "0.1",
        "table_id": "gate5-paper-inclusion",
        "status": "frozen_for_descriptive_rates_only",
        "frozen_date": FROZEN_DATE,
        "boundary": (
            "Frozen current-case inclusion table for Gate 5 descriptive rates only; "
            "not completed statistics, not reviewer agreement, not prevalence, "
            "not source-mix completion, and not paper-grade completion evidence."
        ),
        "source_manifest_ref": rel(manifest_path),
        "paired_runtime_summary_ref": rel(paired_summary_path),
        "claim_boundary": {
            "descriptive_rates_only": True,
            "completed_statistics_claimed": False,
            "reviewer_agreement_claimed": False,
            "prevalence_claim": False,
            "source_mix_completion_claimed": False,
            "paper_grade_completion_claimed": False,
        },
        "declared_case_count": len(entries),
        "entries": entries,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--paired-summary", type=Path, default=DEFAULT_PAIRED_SUMMARY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    manifest_path = args.manifest if args.manifest.is_absolute() else REPO_ROOT / args.manifest
    paired_summary_path = (
        args.paired_summary if args.paired_summary.is_absolute() else REPO_ROOT / args.paired_summary
    )
    output_path = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    table = build_table(manifest_path, paired_summary_path)
    write_json(output_path, table)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
