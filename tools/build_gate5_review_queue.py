#!/usr/bin/env python3
"""Build the Gate 5 manual review queue scaffold."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INCLUSION_TABLE = REPO_ROOT / "benchmark" / "manifests" / "gate5-paper-inclusion.json"
DEFAULT_PAIRED_SUMMARY = REPO_ROOT / "results" / "derived" / "paired-runtime-summary.json"
DEFAULT_ADJUDICATION_FORM = REPO_ROOT / "paper" / "gate5-adjudication-form.md"
DEFAULT_OUTPUT = REPO_ROOT / "benchmark" / "review" / "gate5-review-queue.json"
SOURCE_MIX_LABELS = ["first_party", "public", "synthetic"]
SAMPLE_BATCH_ID = "gate5-current-60-case-review-queue"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def repo_path(ref: str | None) -> Path | None:
    if not isinstance(ref, str) or not ref:
        return None
    return REPO_ROOT / ref.split("#", 1)[0]


def zero_filled_source_mix(counter: Counter[str]) -> dict[str, int]:
    return {label: int(counter.get(label, 0)) for label in SOURCE_MIX_LABELS}


def group_lookup(paired_summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        group["group_key"]: group
        for group in paired_summary.get("groups", [])
        if isinstance(group, dict) and group.get("group_key")
    }


def case_lookup(source_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        case["case_id"]: case
        for case in source_manifest.get("cases", [])
        if isinstance(case, dict) and case.get("case_id")
    }


def review_reasons(group: dict[str, Any] | None) -> list[str]:
    if group is None:
        return ["unmapped_case_metadata_denominator"]

    reasons: list[str] = []
    if int(group.get("runtime_drift_candidate_pairs", 0)) > 0:
        reasons.append("runtime_drift_candidate")
    if int(group.get("pairwise_disagreements", 0)) > 0:
        reasons.append("pairwise_disagreement")
    if int(group.get("realized_contract_violations", 0)) > 0:
        reasons.append("realized_contract_violation")
    if int(group.get("attempted_overreach", 0)) > 0:
        reasons.append("attempted_overreach")
    if int(group.get("missing_expected_outputs", 0)) > 0:
        reasons.append("missing_expected_output")
    if int(group.get("canary_observation_count", 0)) > 0:
        reasons.append("canary_observation")
    if not reasons:
        reasons.append("paired_no_disagreement")
    return reasons


def build_paired_summary(entry: dict[str, Any], group: dict[str, Any] | None) -> dict[str, Any]:
    if group is None:
        return {
            "status": entry["paired_summary_status"],
            "group_key": None,
            "pair_count": 0,
            "runtime_profiles": [],
            "source_comparison_refs": [],
            "runtime_drift_candidate_pairs": 0,
            "pairwise_disagreements": 0,
            "realized_contract_violations": 0,
            "attempted_overreach": 0,
            "missing_expected_outputs": 0,
            "canary_observation_count": 0,
        }

    return {
        "status": "matched_variant_id",
        "group_key": group["group_key"],
        "pair_count": int(group.get("pair_count", 0)),
        "runtime_profiles": sorted(group.get("runtime_profiles", [])),
        "source_comparison_refs": sorted(group.get("source_comparisons", [])),
        "runtime_drift_candidate_pairs": int(group.get("runtime_drift_candidate_pairs", 0)),
        "pairwise_disagreements": int(group.get("pairwise_disagreements", 0)),
        "realized_contract_violations": int(group.get("realized_contract_violations", 0)),
        "attempted_overreach": int(group.get("attempted_overreach", 0)),
        "missing_expected_outputs": int(group.get("missing_expected_outputs", 0)),
        "canary_observation_count": int(group.get("canary_observation_count", 0)),
    }


def build_item(
    index: int,
    entry: dict[str, Any],
    case: dict[str, Any],
    group: dict[str, Any] | None,
    adjudication_form_ref: str,
) -> dict[str, Any]:
    paired_summary = build_paired_summary(entry, group)
    expected_output_path = repo_path(entry.get("expected_output_ref"))
    expected_output_sha256 = sha256_file(expected_output_path) if expected_output_path is not None else None
    source_comparison_sha256s = [
        sha256_file(path)
        for ref in paired_summary["source_comparison_refs"]
        if (path := repo_path(ref)) is not None
    ]
    review_target = "case_plus_paired_summary_packet" if group is not None else "case_metadata_packet"
    blinding = (
        "eligible_for_first_pass_blinding"
        if group is not None and len(paired_summary["runtime_profiles"]) > 1
        else "not_applicable_single_runtime_or_unmapped"
    )
    agreement_scope = (
        "requires_two_independent_human_reviews_before_agreement"
        if group is not None
        else "metadata_only_until_paired_summary_mapping_exists"
    )

    return {
        "review_item_id": f"gate5-review-{index + 1:03d}-{entry['case_id']}",
        "sample_batch_id": SAMPLE_BATCH_ID,
        "case_id": entry["case_id"],
        "case_pointer": entry["case_pointer"],
        "family_id": entry["family_id"],
        "skill_id": entry["skill_id"],
        "task_id": entry["task_id"],
        "contract_id": entry["contract_id"],
        "variant_id": entry["case_id"],
        "category": entry["category"],
        "source_mix_label": entry["source_mix_label"],
        "evidence_stage": entry["evidence_stage"],
        "execution_level": entry["execution_level"],
        "runtime_profiles": entry["runtime_profiles"],
        "review_target": review_target,
        "agreement_scope": agreement_scope,
        "review_reasons": review_reasons(group),
        "review_status": "queued_not_reviewed",
        "runtime_profile_blinding": blinding,
        "paired_summary": paired_summary,
        "refs": {
            "manifest_ref": entry["manifest_ref"],
            "prompt_ref": entry["prompt_ref"],
            "contract_ref": entry["contract_ref"],
            "workspace_ref": entry["workspace_ref"],
            "expected_output_ref": entry["expected_output_ref"],
            "adjudication_form_ref": adjudication_form_ref,
            "hashes": {
                "prompt_sha256": case["task_prompt"]["prompt_sha256"],
                "workspace_snapshot_sha256": case["workspace"]["workspace_snapshot_sha256"],
                "contract_sha256": sha256_file(REPO_ROOT / entry["contract_ref"]),
                "expected_output_sha256": expected_output_sha256,
                "source_comparison_sha256s": source_comparison_sha256s,
            },
        },
        "packet_checks": {
            "publishable_packet_checked": False,
            "trace_finding_refs_expanded": False,
            "real_secrets_allowed": False,
            "synthetic_canary_policy_required": True,
        },
        "review_requirements": [
            "Use paper/gate5-adjudication-form.md for completed review exports.",
            "Blind runtime labels on first-pass review where paired-summary evidence supports it.",
            "Use real independent human reviewer IDs only; agent-assisted triage cannot count toward human agreement.",
            "Do not compute percent agreement or Cohen's kappa until two independent review exports exist for the frozen item set.",
            "Report oracle failures and instrumentation artifacts separately from security findings.",
        ],
    }


def build_queue(
    inclusion_table_path: Path = DEFAULT_INCLUSION_TABLE,
    paired_summary_path: Path = DEFAULT_PAIRED_SUMMARY,
    adjudication_form_path: Path = DEFAULT_ADJUDICATION_FORM,
) -> dict[str, Any]:
    table = load_json(inclusion_table_path)
    paired_summary = load_json(paired_summary_path)
    source_manifest_path = repo_path(table["source_manifest_ref"])
    if source_manifest_path is None:
        raise ValueError("inclusion table source manifest ref is missing")
    source_manifest = load_json(source_manifest_path)
    cases = case_lookup(source_manifest)
    groups = group_lookup(paired_summary)
    adjudication_form_ref = rel(adjudication_form_path)

    included = [
        entry
        for entry in table.get("entries", [])
        if entry.get("included_in_gate5_descriptive_rates") is True
    ]
    review_items: list[dict[str, Any]] = []
    for index, entry in enumerate(included):
        case = cases.get(entry["case_id"])
        if case is None:
            raise KeyError(f"missing source case for {entry['case_id']}")
        group_key = entry.get("paired_summary_group_key")
        group = groups.get(group_key) if isinstance(group_key, str) else None
        review_items.append(build_item(index, entry, case, group, adjudication_form_ref))

    source_mix_counts = zero_filled_source_mix(
        Counter(item["source_mix_label"] for item in review_items)
    )
    aggregate = {
        "included_case_count": len(included),
        "queued_item_count": len(review_items),
        "paired_summary_mapped_item_count": sum(
            1 for item in review_items if item["paired_summary"]["status"] == "matched_variant_id"
        ),
        "paired_summary_unmapped_item_count": sum(
            1
            for item in review_items
            if item["paired_summary"]["status"] == "not_mapped_to_existing_paired_summary_group"
        ),
        "blinding_eligible_item_count": sum(
            1
            for item in review_items
            if item["runtime_profile_blinding"] == "eligible_for_first_pass_blinding"
        ),
        "source_mix_item_counts": source_mix_counts,
        "category_item_counts": dict(sorted(Counter(item["category"] for item in review_items).items())),
        "review_status_counts": dict(sorted(Counter(item["review_status"] for item in review_items).items())),
    }

    return {
        "schema_version": "0.1",
        "queue_id": "gate5-review-queue",
        "status": "queued_not_reviewed",
        "analysis_script": "tools/build_gate5_review_queue.py",
        "boundary": (
            "Gate 5 manual review queue scaffold generated from the frozen inclusion table; "
            "no completed human reviews, reviewer agreement, adjudication, completed statistics, "
            "prevalence, or paper-grade completion claim is made."
        ),
        "input_refs": {
            "frozen_inclusion_table_ref": rel(inclusion_table_path),
            "paired_summary_ref": rel(paired_summary_path),
            "adjudication_form_ref": adjudication_form_ref,
        },
        "sampling_frame": {
            "method": "census_of_included_gate5_cases",
            "selection_rule": "all_cases_in_frozen_inclusion_table_with_included_in_gate5_descriptive_rates_true",
            "random_seed": "not_applicable_census",
            "source_denominator": len(included),
            "selection_locked_before_review": True,
        },
        "claim_boundary": {
            "review_queue_only": True,
            "completed_reviews_claimed": False,
            "reviewer_agreement_claimed": False,
            "adjudication_claimed": False,
            "completed_statistics_claimed": False,
            "prevalence_claim": False,
            "paper_grade_completion_claimed": False,
        },
        "aggregate": aggregate,
        "review_items": review_items,
        "next_dependencies": [
            "Expand each queued item into a sanitized review packet with trace and finding pointers.",
            "Collect two independent real human review exports for the frozen item set before agreement claims.",
            "Adjudicate reviewer disagreements before any adjudicated aggregate is reported.",
            "Keep agent-assisted triage separate from human agreement evidence.",
        ],
    }


def write_markdown(path: Path, queue: dict[str, Any]) -> None:
    aggregate = queue["aggregate"]
    lines = [
        "# Gate 5 Manual Review Queue",
        "",
        queue["boundary"],
        "",
        "## Aggregate",
        "",
        f"- Queued items: `{aggregate['queued_item_count']}`",
        f"- Included cases: `{aggregate['included_case_count']}`",
        f"- Paired-summary mapped items: `{aggregate['paired_summary_mapped_item_count']}`",
        f"- Paired-summary unmapped items: `{aggregate['paired_summary_unmapped_item_count']}`",
        f"- Blinding-eligible items: `{aggregate['blinding_eligible_item_count']}`",
        "- Source-mix items: `first_party={first_party}`, `public={public}`, `synthetic={synthetic}`".format(
            first_party=aggregate["source_mix_item_counts"]["first_party"],
            public=aggregate["source_mix_item_counts"]["public"],
            synthetic=aggregate["source_mix_item_counts"]["synthetic"],
        ),
        "",
        "This artifact is a queue only. It contains no reviewer IDs, completed review results, adjudication records, percent agreement, Cohen's kappa, confidence intervals, hypothesis tests, prevalence estimate, or paper-grade completion claim.",
        "",
        "## Review Items",
        "",
        "| Item | Category | Source mix | Pair status | Blinding | Reasons |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in queue["review_items"]:
        lines.append(
            "| `{item}` | {category} | `{source}` | `{pair}` | `{blind}` | `{reasons}` |".format(
                item=item["review_item_id"],
                category=item["category"],
                source=item["source_mix_label"],
                pair=item["paired_summary"]["status"],
                blind=item["runtime_profile_blinding"],
                reasons=", ".join(item["review_reasons"]),
            )
        )
    lines.extend(["", "## Next Dependencies", ""])
    for dependency in queue["next_dependencies"]:
        lines.append(f"- {dependency}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inclusion-table", type=Path, default=DEFAULT_INCLUSION_TABLE)
    parser.add_argument("--paired-summary", type=Path, default=DEFAULT_PAIRED_SUMMARY)
    parser.add_argument("--adjudication-form", type=Path, default=DEFAULT_ADJUDICATION_FORM)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    inclusion_table_path = (
        args.inclusion_table if args.inclusion_table.is_absolute() else REPO_ROOT / args.inclusion_table
    )
    paired_summary_path = (
        args.paired_summary if args.paired_summary.is_absolute() else REPO_ROOT / args.paired_summary
    )
    adjudication_form_path = (
        args.adjudication_form if args.adjudication_form.is_absolute() else REPO_ROOT / args.adjudication_form
    )
    output_path = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    queue = build_queue(inclusion_table_path, paired_summary_path, adjudication_form_path)
    write_json(output_path, queue)
    write_markdown(output_path.with_suffix(".md"), queue)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
