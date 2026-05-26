#!/usr/bin/env python3
"""Validate the Gate 5 descriptive-rates artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = REPO_ROOT / "results" / "derived" / "gate5-descriptive-rates.json"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import build_gate5_descriptive_rates  # noqa: E402
import validate_gate5_inclusion_table  # noqa: E402
import validate_paired_runtime_summary  # noqa: E402


PROHIBITED_RESULT_KEYS = {
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
    "reviewer_id",
    "reviewer_ids",
    "percent_agreement",
    "cohens_kappa",
    "kappa",
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


def validate_report(path: Path) -> None:
    report = load_json(path)
    require(report.get("schema_version") == "0.1", "schema version mismatch")
    require(report.get("report_type") == "gate5_descriptive_rates", "report type mismatch")
    require(
        report.get("status") == "computed_from_frozen_inclusion_table_no_statistics",
        "status mismatch",
    )
    require(
        report.get("analysis_script") == "tools/build_gate5_descriptive_rates.py",
        "analysis script mismatch",
    )
    boundary = report.get("boundary", "")
    require("Raw descriptive" in boundary, "boundary must state raw descriptive scope")
    require("not completed statistics" in boundary, "boundary must exclude completed statistics")
    require("not reviewer agreement" in boundary, "boundary must exclude reviewer agreement")
    require("not prevalence" in boundary, "boundary must exclude prevalence")

    prohibited = find_prohibited_keys(report)
    require(not prohibited, f"prohibited statistical/reviewer result fields present: {prohibited[:3]}")

    inclusion_table_path = repo_path(report.get("frozen_inclusion_table_ref"))
    paired_summary_path = repo_path(report.get("paired_summary_ref"))
    require(inclusion_table_path is not None and inclusion_table_path.is_file(), "missing inclusion table")
    require(paired_summary_path is not None and paired_summary_path.is_file(), "missing paired summary")
    validate_gate5_inclusion_table.validate_table(inclusion_table_path)
    validate_paired_runtime_summary.validate_summary(paired_summary_path)

    recomputed = build_gate5_descriptive_rates.build_report(inclusion_table_path, paired_summary_path)
    require(report == recomputed, "Gate 5 descriptive-rates report is stale")

    claim_boundary = report.get("claim_boundary", {})
    require(claim_boundary.get("raw_descriptive_rates_only") is True, "raw_descriptive_rates_only must be true")
    for key in (
        "completed_statistics_claimed",
        "confidence_intervals_claimed",
        "hypothesis_tests_claimed",
        "reviewer_agreement_claimed",
        "prevalence_claim",
        "source_mix_completion_claimed",
        "paper_grade_completion_claimed",
    ):
        require(claim_boundary.get(key) is False, f"claim boundary {key} must be false")

    aggregate = report["aggregate"]
    require(
        aggregate["frozen_case_count"] == aggregate["included_case_count"] + aggregate["excluded_case_count"],
        "included/excluded case total mismatch",
    )
    require(
        aggregate["included_case_count"]
        == sum(aggregate["source_mix_case_counts"].values()),
        "source-mix case total mismatch",
    )
    require(
        aggregate["unique_skill_count"]
        == sum(aggregate["source_mix_skill_counts"].values()),
        "source-mix skill total mismatch",
    )
    require(
        aggregate["included_case_count"]
        == aggregate["cases_with_paired_summary_group"] + aggregate["cases_without_paired_summary_group"],
        "paired-summary case total mismatch",
    )
    require(
        aggregate["included_paired_group_count"] == aggregate["cases_with_paired_summary_group"],
        "paired group count mismatch",
    )

    rates = report.get("rates", [])
    require(isinstance(rates, list) and rates, "rates must be non-empty")
    seen_rate_keys: set[tuple[str, str, str]] = set()
    for rate in rates:
        key = (rate["metric_id"], rate["slice"]["dimension"], rate["slice"]["value"])
        require(key not in seen_rate_keys, f"duplicate rate record {key}")
        seen_rate_keys.add(key)
        numerator = rate["numerator"]
        denominator = rate["denominator"]
        require(numerator <= denominator or denominator == 0, f"{key}: numerator exceeds denominator")
        expected_value = round(numerator / denominator, 6) if denominator else 0.0
        require(rate["value"] == expected_value, f"{key}: rate value mismatch")
        require(rate["boundary"] == "raw_descriptive_rate_only_no_statistics", f"{key}: bad boundary")

    required_metrics = {
        "included_case_share",
        "paired_summary_mapped_case_share",
        "source_mix_case_share",
        "source_mix_skill_share",
        "category_case_share",
        "case_status_share",
        "evidence_stage_share",
        "runtime_profile_case_coverage_share",
    }
    observed_metrics = {rate["metric_id"] for rate in rates}
    require(required_metrics.issubset(observed_metrics), f"missing required rate metrics: {sorted(required_metrics - observed_metrics)}")

    markdown_path = path.with_suffix(".md")
    require(markdown_path.is_file(), "missing Gate 5 descriptive-rates Markdown")
    markdown = markdown_path.read_text(encoding="utf-8")
    require(boundary in markdown, "Markdown boundary is stale")
    require(
        f"Included cases: `{aggregate['included_case_count']}`" in markdown,
        "Markdown included-case count is stale",
    )
    require(
        "This artifact reports raw descriptive rates only." in markdown,
        "Markdown descriptive-only boundary missing",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    report_path = args.report if args.report.is_absolute() else REPO_ROOT / args.report
    validate_report(report_path)
    print("validated Gate 5 descriptive rates")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Gate 5 descriptive-rates validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
