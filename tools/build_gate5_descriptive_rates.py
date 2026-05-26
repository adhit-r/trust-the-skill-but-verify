#!/usr/bin/env python3
"""Build raw Gate 5 descriptive rates from the frozen inclusion table."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INCLUSION_TABLE = REPO_ROOT / "benchmark" / "manifests" / "gate5-paper-inclusion.json"
DEFAULT_PAIRED_SUMMARY = REPO_ROOT / "results" / "derived" / "paired-runtime-summary.json"
DEFAULT_OUTPUT = REPO_ROOT / "results" / "derived" / "gate5-descriptive-rates.json"
SOURCE_MIX_LABELS = ["first_party", "public", "synthetic"]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def rate_record(
    metric_id: str,
    dimension: str,
    value: str,
    numerator: int,
    denominator: int,
    unit: str,
) -> dict[str, Any]:
    return {
        "metric_id": metric_id,
        "slice": {"dimension": dimension, "value": value},
        "numerator": numerator,
        "denominator": denominator,
        "value": round(numerator / denominator, 6) if denominator else 0.0,
        "unit": unit,
        "boundary": "raw_descriptive_rate_only_no_statistics",
    }


def zero_filled_source_mix(counter: Counter[str]) -> dict[str, int]:
    return {label: int(counter.get(label, 0)) for label in SOURCE_MIX_LABELS}


def included_entries(table: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        entry
        for entry in table.get("entries", [])
        if entry.get("included_in_gate5_descriptive_rates") is True
    ]


def group_lookup(paired_summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        group["group_key"]: group
        for group in paired_summary.get("groups", [])
        if isinstance(group, dict) and group.get("group_key")
    }


def build_report(
    inclusion_table_path: Path = DEFAULT_INCLUSION_TABLE,
    paired_summary_path: Path = DEFAULT_PAIRED_SUMMARY,
) -> dict[str, Any]:
    table = load_json(inclusion_table_path)
    paired_summary = load_json(paired_summary_path)
    entries = table.get("entries", [])
    included = included_entries(table)
    groups = group_lookup(paired_summary)
    matched_groups = [
        groups[entry["paired_summary_group_key"]]
        for entry in included
        if entry.get("paired_summary_group_key") in groups
    ]

    source_mix_case_counts = zero_filled_source_mix(
        Counter(entry["source_mix_label"] for entry in included)
    )
    skill_to_source_mix = {
        entry["skill_id"]: entry["source_mix_label"]
        for entry in included
    }
    source_mix_skill_counts = zero_filled_source_mix(Counter(skill_to_source_mix.values()))
    runtime_profile_case_counts = Counter(
        profile
        for entry in included
        for profile in entry.get("runtime_profiles", [])
    )

    included_pair_count = sum(int(group.get("pair_count", 0)) for group in matched_groups)
    aggregate = {
        "frozen_case_count": len(entries),
        "included_case_count": len(included),
        "excluded_case_count": len(entries) - len(included),
        "unique_skill_count": len({entry["skill_id"] for entry in included}),
        "source_mix_skill_counts": source_mix_skill_counts,
        "source_mix_case_counts": source_mix_case_counts,
        "case_status_counts": dict(sorted(Counter(entry["case_status"] for entry in included).items())),
        "evidence_stage_counts": dict(sorted(Counter(entry["evidence_stage"] for entry in included).items())),
        "category_case_counts": dict(sorted(Counter(entry["category"] for entry in included).items())),
        "runtime_profile_case_counts": dict(sorted(runtime_profile_case_counts.items())),
        "cases_with_paired_summary_group": sum(
            1 for entry in included if entry.get("paired_summary_group_key") in groups
        ),
        "cases_without_paired_summary_group": sum(
            1 for entry in included if entry.get("paired_summary_group_key") not in groups
        ),
        "included_paired_group_count": len(matched_groups),
        "included_pair_count": included_pair_count,
    }

    rates: list[dict[str, Any]] = []
    rates.append(
        rate_record(
            "included_case_share",
            "all",
            "all",
            aggregate["included_case_count"],
            aggregate["frozen_case_count"],
            "case_share",
        )
    )
    rates.append(
        rate_record(
            "paired_summary_mapped_case_share",
            "all",
            "all",
            aggregate["cases_with_paired_summary_group"],
            aggregate["included_case_count"],
            "case_share",
        )
    )
    for label in SOURCE_MIX_LABELS:
        rates.append(
            rate_record(
                "source_mix_case_share",
                "source_mix_label",
                label,
                source_mix_case_counts[label],
                aggregate["included_case_count"],
                "case_share",
            )
        )
        rates.append(
            rate_record(
                "source_mix_skill_share",
                "source_mix_label",
                label,
                source_mix_skill_counts[label],
                aggregate["unique_skill_count"],
                "skill_share",
            )
        )
    for category, count in aggregate["category_case_counts"].items():
        rates.append(
            rate_record(
                "category_case_share",
                "category",
                category,
                count,
                aggregate["included_case_count"],
                "case_share",
            )
        )
    for status, count in aggregate["case_status_counts"].items():
        rates.append(
            rate_record(
                "case_status_share",
                "case_status",
                status,
                count,
                aggregate["included_case_count"],
                "case_share",
            )
        )
    for stage, count in aggregate["evidence_stage_counts"].items():
        rates.append(
            rate_record(
                "evidence_stage_share",
                "evidence_stage",
                stage,
                count,
                aggregate["included_case_count"],
                "case_share",
            )
        )
    for profile, count in aggregate["runtime_profile_case_counts"].items():
        rates.append(
            rate_record(
                "runtime_profile_case_coverage_share",
                "runtime_profile",
                profile,
                count,
                aggregate["included_case_count"],
                "case_share",
            )
        )
    exclusions = [
        {
            "case_id": entry["case_id"],
            "exclusion_reason": entry["exclusion_reason"] or "unspecified",
        }
        for entry in entries
        if entry.get("included_in_gate5_descriptive_rates") is not True
    ]

    return {
        "schema_version": "0.1",
        "report_type": "gate5_descriptive_rates",
        "status": "computed_from_frozen_inclusion_table_no_statistics",
        "analysis_script": "tools/build_gate5_descriptive_rates.py",
        "boundary": (
            "Raw descriptive denominator and rate artifact built from the frozen Gate 5 inclusion table; "
            "not completed statistics, not confidence intervals, not hypothesis tests, not reviewer "
            "agreement, not prevalence, not source-mix completion, and not paper-grade completion evidence."
        ),
        "input_manifest_refs": [
            table["source_manifest_ref"],
            table["paired_runtime_summary_ref"],
        ],
        "frozen_inclusion_table_ref": rel(inclusion_table_path),
        "paired_summary_ref": rel(paired_summary_path),
        "claim_boundary": {
            "raw_descriptive_rates_only": True,
            "completed_statistics_claimed": False,
            "confidence_intervals_claimed": False,
            "hypothesis_tests_claimed": False,
            "reviewer_agreement_claimed": False,
            "prevalence_claim": False,
            "source_mix_completion_claimed": False,
            "paper_grade_completion_claimed": False,
        },
        "aggregate": aggregate,
        "rates": rates,
        "exclusions": exclusions,
        "next_dependencies": [
            "Add manual review queue and completed two-reviewer records before reviewer agreement claims.",
            "Add public and additional first-party skills before claiming source-mix completion.",
            "Add repeat-backed analysis before Wilson, bootstrap, McNemar, or other statistical claims.",
            "Keep 40/120 full-paper completion blocked until the manifest reaches that floor.",
        ],
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    aggregate = report["aggregate"]
    lines = [
        "# Gate 5 Descriptive Rates",
        "",
        report["boundary"],
        "",
        "## Aggregate",
        "",
        f"- Frozen cases: `{aggregate['frozen_case_count']}`",
        f"- Included cases: `{aggregate['included_case_count']}`",
        f"- Excluded cases: `{aggregate['excluded_case_count']}`",
        f"- Unique skills: `{aggregate['unique_skill_count']}`",
        "- Source-mix skills: `first_party={first_party}`, `public={public}`, `synthetic={synthetic}`".format(
            first_party=aggregate["source_mix_skill_counts"]["first_party"],
            public=aggregate["source_mix_skill_counts"]["public"],
            synthetic=aggregate["source_mix_skill_counts"]["synthetic"],
        ),
        "- Source-mix cases: `first_party={first_party}`, `public={public}`, `synthetic={synthetic}`".format(
            first_party=aggregate["source_mix_case_counts"]["first_party"],
            public=aggregate["source_mix_case_counts"]["public"],
            synthetic=aggregate["source_mix_case_counts"]["synthetic"],
        ),
        f"- Cases with paired-summary group: `{aggregate['cases_with_paired_summary_group']}`",
        f"- Cases without paired-summary group: `{aggregate['cases_without_paired_summary_group']}`",
        f"- Included pair count: `{aggregate['included_pair_count']}`",
        "",
        "This artifact reports raw descriptive rates only. It does not report Wilson intervals, bootstrap intervals, McNemar tests, reviewer agreement, or prevalence.",
        "",
        "## Rates",
        "",
        "| Metric | Slice | Numerator | Denominator | Value |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for rate in report["rates"]:
        lines.append(
            "| `{metric}` | `{dimension}={value}` | {numerator} | {denominator} | {rate_value:.6f} |".format(
                metric=rate["metric_id"],
                dimension=rate["slice"]["dimension"],
                value=rate["slice"]["value"],
                numerator=rate["numerator"],
                denominator=rate["denominator"],
                rate_value=rate["value"],
            )
        )
    lines.extend(["", "## Next Dependencies", ""])
    for dependency in report["next_dependencies"]:
        lines.append(f"- {dependency}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inclusion-table", type=Path, default=DEFAULT_INCLUSION_TABLE)
    parser.add_argument("--paired-summary", type=Path, default=DEFAULT_PAIRED_SUMMARY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    inclusion_table_path = (
        args.inclusion_table if args.inclusion_table.is_absolute() else REPO_ROOT / args.inclusion_table
    )
    paired_summary_path = (
        args.paired_summary if args.paired_summary.is_absolute() else REPO_ROOT / args.paired_summary
    )
    output_path = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    report = build_report(inclusion_table_path, paired_summary_path)
    write_json(output_path, report)
    write_markdown(output_path.with_suffix(".md"), report)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
