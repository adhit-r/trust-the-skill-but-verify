#!/usr/bin/env python3
"""Validate the Gate 5 non-human statistical interval artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = REPO_ROOT / "results" / "derived" / "gate5-statistical-intervals.json"
DEFAULT_SCHEMA = REPO_ROOT / "schemas" / "gate5_statistical_intervals.schema.json"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import build_gate5_statistical_intervals  # noqa: E402
import validate_gate5_descriptive_rates  # noqa: E402
import validate_gate5_inclusion_table  # noqa: E402
import validate_paired_runtime_summary  # noqa: E402


FALSE_CLAIM_KEYS = {
    "mcnemar_hypothesis_tests_claimed",
    "completed_human_review_claimed",
    "reviewer_agreement_claimed",
    "adjudication_claimed",
    "prevalence_claim",
    "source_mix_completion_claimed",
    "paper_grade_completion_claimed",
    "commercial_runtime_behavior_claim",
    "defense_success_claim",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def repo_path(ref: str | None) -> Path | None:
    if not isinstance(ref, str) or not ref:
        return None
    return REPO_ROOT / ref.split("#", 1)[0]


def resolve_pointer(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise ValueError(f"JSON pointer must start with '/': {pointer}")
    value = document
    for raw_part in pointer.lstrip("/").split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            value = value[int(part)]
        elif isinstance(value, dict):
            value = value[part]
        else:
            raise TypeError(f"cannot descend into {type(value).__name__} at {part!r}")
    return value


def validate_interval_record(interval: dict[str, Any], expected_method: str | None = None) -> None:
    metric = interval.get("metric_id", "<unknown>")
    if expected_method is not None:
        require(interval.get("method") == expected_method, f"{metric}: method mismatch")
    require(interval.get("confidence_level") == 0.95, f"{metric}: confidence level mismatch")
    require(0 <= interval["lower"] <= interval["estimate"] <= interval["upper"] <= 1, f"{metric}: bad interval bounds")
    require(interval.get("boundary") == build_gate5_statistical_intervals.INTERVAL_BOUNDARY, f"{metric}: bad boundary")
    source = repo_path(interval.get("source"))
    require(source is not None and source.is_file(), f"{metric}: missing source file")
    resolve_pointer(load_json(source), interval["source_pointer"])
    if "numerator" in interval:
        numerator = interval["numerator"]
        denominator = interval["denominator"]
        require(isinstance(numerator, int) and isinstance(denominator, int), f"{metric}: bad numerator/denominator")
        require(0 <= numerator <= denominator, f"{metric}: numerator exceeds denominator")
        expected_estimate, expected_lower, expected_upper = build_gate5_statistical_intervals.wilson_bounds(
            numerator,
            denominator,
        )
        require(interval["estimate"] == expected_estimate, f"{metric}: estimate mismatch")
        require(interval["lower"] == expected_lower, f"{metric}: lower bound mismatch")
        require(interval["upper"] == expected_upper, f"{metric}: upper bound mismatch")
    if "sample_count" in interval:
        require(
            interval["sample_count"] == build_gate5_statistical_intervals.BOOTSTRAP_SAMPLES,
            f"{metric}: bootstrap sample count mismatch",
        )


def validate_report(path: Path) -> None:
    schema = load_json(DEFAULT_SCHEMA)
    require(schema.get("title") == "Gate 5 Statistical Intervals", "schema title mismatch")

    report = load_json(path)
    require(report.get("schema_version") == "0.1", "schema version mismatch")
    require(report.get("report_type") == "gate5_statistical_intervals", "report type mismatch")
    require(report.get("status") == "non_human_intervals_ready_no_manual_review", "status mismatch")
    require(
        report.get("analysis_script") == "tools/build_gate5_statistical_intervals.py",
        "analysis script mismatch",
    )
    boundary = report.get("boundary", "")
    for required_text in (
        "Non-human Wilson and bootstrap interval artifact",
        "not an ecosystem prevalence estimate",
        "not a completed human/manual review",
        "Human review remains 0%",
    ):
        require(required_text in boundary, f"boundary missing {required_text!r}")

    input_refs = report.get("input_refs", {})
    inclusion_table_path = repo_path(input_refs.get("frozen_inclusion_table_ref"))
    descriptive_rates_path = repo_path(input_refs.get("descriptive_rates_ref"))
    paired_summary_path = repo_path(input_refs.get("paired_runtime_summary_ref"))
    require(inclusion_table_path is not None and inclusion_table_path.is_file(), "missing inclusion table")
    require(descriptive_rates_path is not None and descriptive_rates_path.is_file(), "missing descriptive rates")
    require(paired_summary_path is not None and paired_summary_path.is_file(), "missing paired summary")
    validate_gate5_inclusion_table.validate_table(inclusion_table_path)
    validate_paired_runtime_summary.validate_summary(paired_summary_path)
    validate_gate5_descriptive_rates.validate_report(descriptive_rates_path)

    recomputed = build_gate5_statistical_intervals.build_report(
        inclusion_table_path,
        descriptive_rates_path,
        paired_summary_path,
    )
    require(report == recomputed, "Gate 5 statistical-interval report is stale")

    claim_boundary = report.get("claim_boundary", {})
    for key in (
        "non_human_interval_statistics_claimed",
        "wilson_intervals_claimed",
        "bootstrap_intervals_claimed",
        "hierarchical_bootstrap_intervals_claimed",
    ):
        require(claim_boundary.get(key) is True, f"claim boundary {key} must be true")
    for key in FALSE_CLAIM_KEYS:
        require(claim_boundary.get(key) is False, f"claim boundary {key} must be false")

    aggregate = report["aggregate"]
    descriptive_rates = load_json(descriptive_rates_path)
    paired_summary = load_json(paired_summary_path)
    require(
        aggregate["frozen_case_count"] == descriptive_rates["aggregate"]["frozen_case_count"],
        "frozen case count mismatch",
    )
    require(
        aggregate["included_case_count"] == descriptive_rates["aggregate"]["included_case_count"],
        "included case count mismatch",
    )
    require(
        aggregate["paired_summary_pair_count"] == paired_summary["aggregate"]["pair_count"],
        "paired summary pair count mismatch",
    )
    require(
        aggregate["wilson_interval_count"] == len(report["wilson_intervals"]),
        "Wilson interval count mismatch",
    )
    require(
        aggregate["case_bootstrap_interval_count"] == len(report["case_bootstrap_intervals"]),
        "case bootstrap interval count mismatch",
    )
    require(
        aggregate["hierarchical_bootstrap_interval_count"] == len(report["hierarchical_bootstrap_intervals"]),
        "hierarchical bootstrap interval count mismatch",
    )
    require(aggregate["mcnemar_result_count"] == 0, "McNemar results must remain zero")
    require(aggregate["completed_human_review_count"] == 0, "human review count must remain zero")
    require(aggregate["reviewer_agreement_result_count"] == 0, "reviewer agreement count must remain zero")

    wilson_intervals = report.get("wilson_intervals", [])
    case_bootstrap_intervals = report.get("case_bootstrap_intervals", [])
    hierarchical_bootstrap_intervals = report.get("hierarchical_bootstrap_intervals", [])
    require(len(wilson_intervals) >= len(descriptive_rates["rates"]), "missing descriptive Wilson intervals")
    require(case_bootstrap_intervals, "missing case bootstrap intervals")
    require(hierarchical_bootstrap_intervals, "missing hierarchical bootstrap intervals")
    for interval in wilson_intervals:
        validate_interval_record(interval, "wilson_score")
    for interval in case_bootstrap_intervals:
        validate_interval_record(interval, "nonparametric_case_bootstrap")
    for interval in hierarchical_bootstrap_intervals:
        validate_interval_record(interval, "hierarchical_skill_case_bootstrap")

    paired = report["paired_runtime_summary"]
    require(paired["pair_count"] == paired_summary["aggregate"]["pair_count"], "paired pair count mismatch")
    require(
        sum(paired["classification_counts"].values()) == paired["pair_count"],
        "paired classification counts must sum to pair count",
    )
    require(
        sum(paired["runtime_pair_counts"].values()) == paired["pair_count"],
        "runtime pair counts must sum to pair count",
    )
    require(
        sum(paired["pair_max_severity_counts"].values()) == paired["pair_count"],
        "severity counts must sum to pair count",
    )
    require(
        paired["max_pair_severity"] in paired["pair_max_severity_counts"],
        "max severity must be represented in severity counts",
    )
    require(
        "not human-adjudicated severity" in paired["max_severity_reporting_boundary"],
        "max severity boundary missing",
    )

    mcnemar = report["mcnemar_style_analysis"]
    require(mcnemar["status"] == "deferred_not_reported", "McNemar status mismatch")
    require(mcnemar["result_count"] == 0, "McNemar result count must be zero")
    require("not a frozen binary human-adjudicated matched outcome table" in mcnemar["reason"], "McNemar boundary missing")

    manual = report["manual_review_status"]
    require(manual["completed_human_review_count"] == 0, "manual review count must be zero")
    require(manual["percent_complete"] == 0.0, "manual review percent must be zero")
    require("Human/manual review remains 0%" in manual["boundary"], "manual review boundary missing")

    markdown_path = path.with_suffix(".md")
    require(markdown_path.is_file(), "missing Gate 5 statistical intervals Markdown")
    markdown = markdown_path.read_text(encoding="utf-8")
    require(boundary in markdown, "Markdown boundary is stale")
    require(
        f"Wilson intervals: `{aggregate['wilson_interval_count']}`" in markdown,
        "Markdown Wilson count is stale",
    )
    require("Human/manual review: `0.0%` complete" in markdown, "Markdown human-review boundary missing")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    report_path = args.report if args.report.is_absolute() else REPO_ROOT / args.report
    validate_report(report_path)
    print("validated Gate 5 statistical intervals")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Gate 5 statistical-interval validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
