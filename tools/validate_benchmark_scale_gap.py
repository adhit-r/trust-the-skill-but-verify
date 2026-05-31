#!/usr/bin/env python3
"""Validate the derived benchmark-scale gap report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = REPO_ROOT / "results" / "derived" / "benchmark-scale-gap.json"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import build_benchmark_scale_gap  # noqa: E402
import validate_benchmark_cases  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_target(target_id: str, target: dict[str, Any]) -> None:
    category_distribution = target.get("category_distribution")
    source_mix = target.get("source_mix_target")
    require(isinstance(category_distribution, dict), f"{target_id}: category distribution missing")
    require(isinstance(source_mix, dict), f"{target_id}: source mix missing")
    require(
        sorted(category_distribution) == sorted(build_benchmark_scale_gap.CATEGORIES),
        f"{target_id}: category set mismatch",
    )
    require(
        sorted(source_mix) == sorted(build_benchmark_scale_gap.SOURCE_MIX_LABELS),
        f"{target_id}: source mix label set mismatch",
    )
    require(
        sum(category_distribution.values()) == target["target_skill_category_total"],
        f"{target_id}: category target total mismatch",
    )
    require(
        sum(source_mix.values()) == target["target_source_mix_total"],
        f"{target_id}: source mix total mismatch",
    )
    require(
        target["target_skill_count"] * target["triples_per_skill"] == target["target_triple_count"],
        f"{target_id}: skill/triple target mismatch",
    )
    require(
        sum(target["skill_category_gaps"].values()) == target["skill_category_shortfall"],
        f"{target_id}: category gap total mismatch",
    )
    require(
        sorted(target["source_mix_skill_gaps"]) == sorted(build_benchmark_scale_gap.SOURCE_MIX_LABELS),
        f"{target_id}: source mix gap label set mismatch",
    )
    require(
        sum(target["source_mix_skill_gaps"].values()) == target["source_mix_skill_shortfall"],
        f"{target_id}: source mix gap total mismatch",
    )
    require(
        target["skill_shortfall"] <= target["skill_category_shortfall"],
        f"{target_id}: skill shortfall cannot exceed category gap total",
    )
    require(
        target["triple_shortfall"] >= target["skill_shortfall"],
        f"{target_id}: triple shortfall should be at least skill shortfall before target completion",
    )
    require(
        target["source_mix_gap_status"] == "computed_from_explicit_case_source_mix_labels_no_completion_claim",
        f"{target_id}: source-mix gap must be computed without claiming completion",
    )


def validate_report(path: Path) -> None:
    report = load_json(path)
    require(report.get("schema_version") == "0.1", "schema version mismatch")
    require(report.get("report_type") == "benchmark_scale_gap", "report type mismatch")
    boundary = report.get("boundary", "")
    require("not proof" in boundary, "boundary must exclude target completion proof")
    require("20/60" in boundary and "40/120" in boundary, "boundary must name scale floors")
    require(
        "skill-origin/source-mix accounting label" in report.get("source_mix_label_scope", ""),
        "source-mix label scope must define skill-origin accounting",
    )

    source_manifest_path = REPO_ROOT / report["source_manifest"]
    source_manifest = validate_benchmark_cases.load_json(source_manifest_path)
    schema = validate_benchmark_cases.load_schema()
    source_issues = validate_benchmark_cases.validate_manifest(source_manifest, source_manifest_path, schema)
    first_issue = source_issues[0] if source_issues else None
    require(not source_issues, f"source manifest failed benchmark validation: {first_issue}")

    recomputed = build_benchmark_scale_gap.build_report(source_manifest_path)
    require(report == recomputed, "benchmark scale gap report is stale")

    claim_boundary = report.get("claim_boundary", {})
    for key in (
        "mid_scale_floor_claimed",
        "full_paper_floor_claimed",
        "prevalence_claim",
        "source_mix_gap_claimed",
        "source_mix_completion_claimed",
        "current_entries_are_skill_count_claim",
        "current_entries_are_triple_count_claim",
    ):
        require(claim_boundary.get(key) is False, f"claim boundary {key} must be false")
    require(claim_boundary.get("source_mix_gap_computed") is True, "claim boundary source_mix_gap_computed must be true")

    current = report["current"]
    require(current["case_entry_count"] == current["declared_case_count"], "current count mismatch")
    require(current["case_entry_count"] == sum(current["triple_category_counts"].values()), "triple category count total mismatch")
    require(current["unique_skill_count"] == sum(current["skill_category_counts"].values()), "skill category count total mismatch")
    require(current["case_entry_count"] == sum(current["source_mix_case_counts"].values()), "source mix case count total mismatch")
    require(current["unique_skill_count"] == sum(current["source_mix_skill_counts"].values()), "source mix skill count total mismatch")
    require(current["multi_source_mix_skills"] == [], f"source mix labels must be single-label per counted skill: {current['multi_source_mix_skills']}")
    require(current["unique_skill_count"] <= current["case_entry_count"], "skill count cannot exceed case entries")
    require(
        current["unique_skill_task_contract_triple_count"] <= current["case_entry_count"],
        "triple count cannot exceed case entries",
    )
    require(
        current["missing_categories"] == [],
        f"all normalized categories must have at least one current inclusion entry; missing {current['missing_categories']}",
    )

    targets = report["targets"]
    validate_target("mid_scale_20_60", targets["mid_scale_20_60"])
    validate_target("full_paper_40_120", targets["full_paper_40_120"])
    require(targets["mid_scale_20_60"]["target_skill_count"] == 20, "mid-scale skill target mismatch")
    require(targets["mid_scale_20_60"]["target_triple_count"] == 60, "mid-scale triple target mismatch")
    require(targets["full_paper_40_120"]["target_skill_count"] == 40, "full-paper skill target mismatch")
    require(targets["full_paper_40_120"]["target_triple_count"] == 120, "full-paper triple target mismatch")

    markdown_path = path.with_suffix(".md")
    require(markdown_path.is_file(), "missing benchmark scale gap Markdown")
    markdown = markdown_path.read_text(encoding="utf-8")
    require(report["boundary"] in markdown, "Markdown boundary is stale")
    require(f"Mid-scale skill shortfall: `{targets['mid_scale_20_60']['skill_shortfall']}`" in markdown, "Markdown mid-scale skill shortfall is stale")
    require(f"Mid-scale triple shortfall: `{targets['mid_scale_20_60']['triple_shortfall']}`" in markdown, "Markdown mid-scale triple shortfall is stale")
    require(
        f"Mid-scale source-mix skill shortfall: `{targets['mid_scale_20_60']['source_mix_skill_shortfall']}`" in markdown,
        "Markdown mid-scale source-mix shortfall is stale",
    )
    require(
        "Source-mix gaps are computed from explicit manifest labels" in markdown,
        "Markdown source-mix boundary is stale",
    )
    require("This artifact does not claim benchmark prevalence" in markdown, "Markdown claim boundary missing")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    report_path = args.report if args.report.is_absolute() else REPO_ROOT / args.report
    validate_report(report_path)
    print("validated benchmark scale gap report")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"benchmark scale gap validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
