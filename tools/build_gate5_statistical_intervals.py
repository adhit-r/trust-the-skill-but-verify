#!/usr/bin/env python3
"""Build bounded Gate 5 non-human statistical interval artifacts."""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INCLUSION_TABLE = REPO_ROOT / "benchmark" / "manifests" / "gate5-paper-inclusion.json"
DEFAULT_DESCRIPTIVE_RATES = REPO_ROOT / "results" / "derived" / "gate5-descriptive-rates.json"
DEFAULT_PAIRED_SUMMARY = REPO_ROOT / "results" / "derived" / "paired-runtime-summary.json"
DEFAULT_OUTPUT = REPO_ROOT / "results" / "derived" / "gate5-statistical-intervals.json"
EXCLUDED_COMPARISON_PREFIXES = (
    REPO_ROOT / "results" / "fixtures" / "strengthening" / "source-mix-rp6-report-card",
)
CONFIDENCE_LEVEL = 0.95
WILSON_Z = 1.959963984540054
BOOTSTRAP_SAMPLES = 2000
BOOTSTRAP_SEED = 20260528
INTERVAL_BOUNDARY = (
    "curated_gate5_denominator_only_not_prevalence_not_human_review_not_adjudication"
)
SEVERITY_RANK = {
    "none": 0,
    "info": 1,
    "informational": 1,
    "low": 2,
    "medium": 3,
    "high": 4,
    "critical": 5,
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def round6(value: float) -> float:
    return round(float(value), 6)


def wilson_bounds(numerator: int, denominator: int) -> tuple[float, float, float]:
    if denominator <= 0:
        return 0.0, 0.0, 0.0
    estimate = numerator / denominator
    z2 = WILSON_Z * WILSON_Z
    denom = 1 + z2 / denominator
    center = (estimate + z2 / (2 * denominator)) / denom
    half_width = (
        WILSON_Z
        * math.sqrt((estimate * (1 - estimate) / denominator) + (z2 / (4 * denominator * denominator)))
        / denom
    )
    return round6(estimate), round6(max(0.0, center - half_width)), round6(min(1.0, center + half_width))


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    position = (len(sorted_values) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return round6(sorted_values[lower])
    lower_value = sorted_values[lower]
    upper_value = sorted_values[upper]
    weight = position - lower
    return round6(lower_value + (upper_value - lower_value) * weight)


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


def wilson_record(
    metric_id: str,
    dimension: str,
    value: str,
    numerator: int,
    denominator: int,
    unit: str,
    source: str,
    source_pointer: str,
) -> dict[str, Any]:
    estimate, lower, upper = wilson_bounds(numerator, denominator)
    return {
        "metric_id": metric_id,
        "slice": {"dimension": dimension, "value": value},
        "method": "wilson_score",
        "confidence_level": CONFIDENCE_LEVEL,
        "numerator": numerator,
        "denominator": denominator,
        "estimate": estimate,
        "lower": lower,
        "upper": upper,
        "unit": unit,
        "source": source,
        "source_pointer": source_pointer,
        "boundary": INTERVAL_BOUNDARY,
    }


def bootstrap_record(
    metric_id: str,
    dimension: str,
    value: str,
    samples: list[float],
    observed_estimate: float,
    unit: str,
    method: str,
    source: str,
    source_pointer: str,
) -> dict[str, Any]:
    return {
        "metric_id": metric_id,
        "slice": {"dimension": dimension, "value": value},
        "method": method,
        "confidence_level": CONFIDENCE_LEVEL,
        "sample_count": len(samples),
        "estimate": round6(observed_estimate),
        "lower": percentile(samples, 0.025),
        "upper": percentile(samples, 0.975),
        "unit": unit,
        "source": source,
        "source_pointer": source_pointer,
        "boundary": INTERVAL_BOUNDARY,
    }


def case_metric_predicate(rate: dict[str, Any], groups: dict[str, dict[str, Any]]) -> Callable[[dict[str, Any]], bool] | None:
    metric_id = rate["metric_id"]
    dimension = rate["slice"]["dimension"]
    value = rate["slice"]["value"]
    if metric_id == "paired_summary_mapped_case_share":
        return lambda entry: entry.get("paired_summary_group_key") in groups
    if metric_id in {"source_mix_case_share", "category_case_share", "case_status_share", "evidence_stage_share"}:
        field = {
            "source_mix_label": "source_mix_label",
            "category": "category",
            "case_status": "case_status",
            "evidence_stage": "evidence_stage",
        }.get(dimension)
        if field is None:
            return None
        return lambda entry: entry.get(field) == value
    if metric_id == "runtime_profile_case_coverage_share":
        return lambda entry: value in entry.get("runtime_profiles", [])
    return None


def pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def case_bootstrap_intervals(
    entries: list[dict[str, Any]],
    rates: list[dict[str, Any]],
    groups: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    rng = random.Random(BOOTSTRAP_SEED)
    case_rates = [
        rate
        for rate in rates
        if rate.get("unit") == "case_share"
        and rate.get("metric_id") != "included_case_share"
        and case_metric_predicate(rate, groups) is not None
    ]
    rate_positions = {id(rate): index for index, rate in enumerate(rates)}
    for rate in case_rates:
        predicate = case_metric_predicate(rate, groups)
        if predicate is None:
            continue
        samples: list[float] = []
        for _ in range(BOOTSTRAP_SAMPLES):
            sample = [rng.choice(entries) for _ in range(len(entries))]
            samples.append(sum(1 for entry in sample if predicate(entry)) / len(sample))
        records.append(
            bootstrap_record(
                rate["metric_id"],
                rate["slice"]["dimension"],
                rate["slice"]["value"],
                samples,
                rate["value"],
                rate["unit"],
                "nonparametric_case_bootstrap",
                "results/derived/gate5-descriptive-rates.json",
                f"/rates/{rate_positions[id(rate)]}",
            )
        )
    return records


def hierarchical_bootstrap_intervals(
    entries: list[dict[str, Any]],
    rates: list[dict[str, Any]],
    groups: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    rng = random.Random(BOOTSTRAP_SEED + 1)
    entries_by_skill: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        entries_by_skill[entry["skill_id"]].append(entry)
    skill_ids = sorted(entries_by_skill)
    selected_rates = [
        rate
        for rate in rates
        if rate.get("unit") == "case_share"
        and rate.get("metric_id")
        in {"paired_summary_mapped_case_share", "source_mix_case_share", "evidence_stage_share"}
        and case_metric_predicate(rate, groups) is not None
    ]
    rate_positions = {id(rate): index for index, rate in enumerate(rates)}
    for rate in selected_rates:
        predicate = case_metric_predicate(rate, groups)
        if predicate is None:
            continue
        samples: list[float] = []
        for _ in range(BOOTSTRAP_SAMPLES):
            sampled_entries: list[dict[str, Any]] = []
            for skill_id in (rng.choice(skill_ids) for _ in range(len(skill_ids))):
                skill_entries = entries_by_skill[skill_id]
                sampled_entries.extend(rng.choice(skill_entries) for _ in range(len(skill_entries)))
            samples.append(
                sum(1 for entry in sampled_entries if predicate(entry)) / len(sampled_entries)
                if sampled_entries
                else 0.0
            )
        records.append(
            bootstrap_record(
                rate["metric_id"],
                rate["slice"]["dimension"],
                rate["slice"]["value"],
                samples,
                rate["value"],
                rate["unit"],
                "hierarchical_skill_case_bootstrap",
                "results/derived/gate5-descriptive-rates.json",
                f"/rates/{rate_positions[id(rate)]}",
            )
        )
    return records


def comparison_files() -> list[Path]:
    return sorted(
        path
        for path in REPO_ROOT.glob("results/**/*.json")
        if path.name.endswith("_comparison.json")
        and not any(path.is_relative_to(prefix) for prefix in EXCLUDED_COMPARISON_PREFIXES)
    )


def pair_max_severity(pair: dict[str, Any]) -> str:
    max_seen = "none"
    for side in ("only_in_left", "only_in_right"):
        for finding in pair.get(side, []):
            if not isinstance(finding, dict):
                continue
            severity = str(finding.get("severity") or "none").lower()
            if SEVERITY_RANK.get(severity, 0) > SEVERITY_RANK[max_seen]:
                max_seen = severity
    return max_seen


def paired_records_from_comparisons() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for comparison_path in comparison_files():
        comparison = load_json(comparison_path)
        for pair in comparison.get("pairs", []):
            records.append(
                {
                    "source_comparison": rel(comparison_path),
                    "runtime_pair": f"{pair['left_runtime_profile']}__{pair['right_runtime_profile']}",
                    "classification": pair.get("classification", {}).get("claim") or "unknown",
                    "disagreement_count": int(pair.get("disagreement_count", 0)),
                    "max_severity": pair_max_severity(pair),
                }
            )
    return records


def paired_runtime_intervals(
    paired_summary: dict[str, Any],
    paired_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    aggregate = paired_summary["aggregate"]
    denominator = int(aggregate["pair_count"])
    intervals: list[dict[str, Any]] = []
    for classification, count in aggregate["classification_counts"].items():
        intervals.append(
            wilson_record(
                "pair_classification_share",
                "classification",
                classification,
                int(count),
                denominator,
                "pair_share",
                "results/derived/paired-runtime-summary.json",
                f"/aggregate/classification_counts/{pointer_escape(str(classification))}",
            )
        )
    for runtime_pair, count in aggregate["runtime_pair_counts"].items():
        intervals.append(
            wilson_record(
                "runtime_pair_share",
                "runtime_pair",
                runtime_pair,
                int(count),
                denominator,
                "pair_share",
                "results/derived/paired-runtime-summary.json",
                f"/aggregate/runtime_pair_counts/{pointer_escape(str(runtime_pair))}",
            )
        )
    positive_disagreement_count = sum(1 for record in paired_records if record["disagreement_count"] > 0)
    intervals.append(
        wilson_record(
            "positive_pair_disagreement_share",
            "all",
            "all",
            positive_disagreement_count,
            denominator,
            "pair_share",
            "results/derived/paired-runtime-summary.json",
            "/aggregate/pair_count",
        )
    )
    severity_counts = Counter(record["max_severity"] for record in paired_records)
    for severity in sorted(severity_counts, key=lambda item: (SEVERITY_RANK.get(item, 0), item)):
        intervals.append(
            wilson_record(
                "pair_max_severity_share",
                "max_severity",
                severity,
                int(severity_counts[severity]),
                denominator,
                "pair_share",
                "results/derived/paired-runtime-summary.json",
                "/aggregate/pair_count",
            )
        )
    return intervals


def paired_runtime_summary(paired_summary: dict[str, Any], paired_records: list[dict[str, Any]]) -> dict[str, Any]:
    aggregate = paired_summary["aggregate"]
    disagreement_counts = [record["disagreement_count"] for record in paired_records]
    classification_counts = Counter(record["classification"] for record in paired_records)
    severity_counts = Counter(record["max_severity"] for record in paired_records)
    max_severity = max(severity_counts, key=lambda item: (SEVERITY_RANK.get(item, 0), item)) if severity_counts else "none"
    majority_classification = (
        classification_counts.most_common(1)[0][0] if classification_counts else "none"
    )
    return {
        "pair_count": int(aggregate["pair_count"]),
        "runtime_pair_counts": aggregate["runtime_pair_counts"],
        "classification_counts": dict(sorted(classification_counts.items())),
        "positive_pair_disagreement_count": sum(1 for count in disagreement_counts if count > 0),
        "pairwise_disagreement_finding_count": int(aggregate["pairwise_disagreement_count"]),
        "median_pair_disagreement_count": round6(statistics.median(disagreement_counts)) if disagreement_counts else 0.0,
        "majority_pair_classification": majority_classification,
        "pair_max_severity_counts": dict(
            sorted(severity_counts.items(), key=lambda item: (SEVERITY_RANK.get(item[0], 0), item[0]))
        ),
        "max_pair_severity": max_severity,
        "max_severity_reporting_boundary": (
            "Max severity is computed from comparator finding-set deltas only; it is reported beside "
            "majority/median behavior and is not human-adjudicated severity."
        ),
    }


def build_report(
    inclusion_table_path: Path = DEFAULT_INCLUSION_TABLE,
    descriptive_rates_path: Path = DEFAULT_DESCRIPTIVE_RATES,
    paired_summary_path: Path = DEFAULT_PAIRED_SUMMARY,
) -> dict[str, Any]:
    table = load_json(inclusion_table_path)
    descriptive_rates = load_json(descriptive_rates_path)
    paired_summary = load_json(paired_summary_path)
    entries = included_entries(table)
    groups = group_lookup(paired_summary)
    rates = descriptive_rates.get("rates", [])

    wilson_intervals = []
    for index, rate in enumerate(rates):
        wilson_intervals.append(
            wilson_record(
                rate["metric_id"],
                rate["slice"]["dimension"],
                rate["slice"]["value"],
                int(rate["numerator"]),
                int(rate["denominator"]),
                rate["unit"],
                "results/derived/gate5-descriptive-rates.json",
                f"/rates/{index}",
            )
        )
    paired_records = paired_records_from_comparisons()
    wilson_intervals.extend(paired_runtime_intervals(paired_summary, paired_records))
    case_bootstrap = case_bootstrap_intervals(entries, rates, groups)
    hierarchical_bootstrap = hierarchical_bootstrap_intervals(entries, rates, groups)
    paired_summary_section = paired_runtime_summary(paired_summary, paired_records)

    return {
        "schema_version": "0.1",
        "report_type": "gate5_statistical_intervals",
        "status": "non_human_intervals_ready_no_manual_review",
        "analysis_script": "tools/build_gate5_statistical_intervals.py",
        "boundary": (
            "Non-human Wilson and bootstrap interval artifact over the curated Gate 5 denominator and "
            "existing paired-runtime summary. It is not an ecosystem prevalence estimate, not a "
            "completed human/manual review, not reviewer agreement, not adjudication, not a McNemar "
            "hypothesis-test result, not source-mix evidence completion, not commercial-runtime "
            "behavior, not defense-success evidence, and not paper-grade completion by itself. Human "
            "review remains 0% until real reviewers complete the review exports."
        ),
        "input_refs": {
            "frozen_inclusion_table_ref": rel(inclusion_table_path),
            "descriptive_rates_ref": rel(descriptive_rates_path),
            "paired_runtime_summary_ref": rel(paired_summary_path),
        },
        "parameters": {
            "confidence_level": CONFIDENCE_LEVEL,
            "wilson_z": WILSON_Z,
            "bootstrap_samples": BOOTSTRAP_SAMPLES,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "bootstrap_quantiles": [0.025, 0.975],
        },
        "claim_boundary": {
            "non_human_interval_statistics_claimed": True,
            "wilson_intervals_claimed": True,
            "bootstrap_intervals_claimed": True,
            "hierarchical_bootstrap_intervals_claimed": True,
            "mcnemar_hypothesis_tests_claimed": False,
            "completed_human_review_claimed": False,
            "reviewer_agreement_claimed": False,
            "adjudication_claimed": False,
            "prevalence_claim": False,
            "source_mix_completion_claimed": False,
            "paper_grade_completion_claimed": False,
            "commercial_runtime_behavior_claim": False,
            "defense_success_claim": False,
        },
        "aggregate": {
            "frozen_case_count": int(descriptive_rates["aggregate"]["frozen_case_count"]),
            "included_case_count": int(descriptive_rates["aggregate"]["included_case_count"]),
            "unique_skill_count": int(descriptive_rates["aggregate"]["unique_skill_count"]),
            "paired_summary_mapped_case_count": int(
                descriptive_rates["aggregate"]["cases_with_paired_summary_group"]
            ),
            "paired_summary_unmapped_case_count": int(
                descriptive_rates["aggregate"]["cases_without_paired_summary_group"]
            ),
            "paired_summary_pair_count": int(paired_summary["aggregate"]["pair_count"]),
            "wilson_interval_count": len(wilson_intervals),
            "case_bootstrap_interval_count": len(case_bootstrap),
            "hierarchical_bootstrap_interval_count": len(hierarchical_bootstrap),
            "mcnemar_result_count": 0,
            "mcnemar_deferred_count": 1,
            "completed_human_review_count": 0,
            "reviewer_agreement_result_count": 0,
        },
        "wilson_intervals": wilson_intervals,
        "case_bootstrap_intervals": case_bootstrap,
        "hierarchical_bootstrap_intervals": hierarchical_bootstrap,
        "paired_runtime_summary": paired_summary_section,
        "mcnemar_style_analysis": {
            "status": "deferred_not_reported",
            "result_count": 0,
            "reason": (
                "Current paired-runtime records are comparator classifications and finding-set deltas, "
                "not a frozen binary human-adjudicated matched outcome table. A McNemar-style result "
                "would overstate the evidence at this stage."
            ),
        },
        "manual_review_status": {
            "completed_human_review_count": 0,
            "percent_complete": 0.0,
            "boundary": "Human/manual review remains 0% until real independent reviewers complete exports.",
        },
        "next_dependencies": [
            "Complete real two-reviewer human review exports before reviewer agreement or Cohen's kappa claims.",
            "Add binary matched outcome labels before McNemar-style hypothesis-test reporting.",
            "Keep all intervals scoped to the curated Gate 5 denominator rather than ecosystem prevalence.",
            "Promote more source-provenance entries into executable evidence before claiming source-mix evidence completion.",
        ],
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    aggregate = report["aggregate"]
    paired = report["paired_runtime_summary"]
    lines = [
        "# Gate 5 Statistical Intervals",
        "",
        report["boundary"],
        "",
        "## Aggregate",
        "",
        f"- Frozen cases: `{aggregate['frozen_case_count']}`",
        f"- Included cases: `{aggregate['included_case_count']}`",
        f"- Unique skills: `{aggregate['unique_skill_count']}`",
        f"- Paired-summary mapped cases: `{aggregate['paired_summary_mapped_case_count']}`",
        f"- Paired-summary unmapped cases: `{aggregate['paired_summary_unmapped_case_count']}`",
        f"- Paired-runtime pair records: `{aggregate['paired_summary_pair_count']}`",
        f"- Wilson intervals: `{aggregate['wilson_interval_count']}`",
        f"- Case bootstrap intervals: `{aggregate['case_bootstrap_interval_count']}`",
        f"- Hierarchical bootstrap intervals: `{aggregate['hierarchical_bootstrap_interval_count']}`",
        f"- McNemar results: `{aggregate['mcnemar_result_count']}`",
        f"- Completed human reviews: `{aggregate['completed_human_review_count']}`",
        "",
        "## Paired Runtime Summary",
        "",
        f"- Majority pair classification: `{paired['majority_pair_classification']}`",
        f"- Median pair disagreement count: `{paired['median_pair_disagreement_count']:.6f}`",
        f"- Positive disagreement pairs: `{paired['positive_pair_disagreement_count']}`",
        f"- Pairwise disagreement finding count: `{paired['pairwise_disagreement_finding_count']}`",
        f"- Max pair severity: `{paired['max_pair_severity']}`",
        "",
        paired["max_severity_reporting_boundary"],
        "",
        "## Wilson Intervals",
        "",
        "| Metric | Slice | Numerator | Denominator | Estimate | 95% Lower | 95% Upper |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for interval in report["wilson_intervals"]:
        lines.append(
            "| `{metric}` | `{dimension}={value}` | {numerator} | {denominator} | {estimate:.6f} | {lower:.6f} | {upper:.6f} |".format(
                metric=interval["metric_id"],
                dimension=interval["slice"]["dimension"],
                value=interval["slice"]["value"],
                numerator=interval["numerator"],
                denominator=interval["denominator"],
                estimate=interval["estimate"],
                lower=interval["lower"],
                upper=interval["upper"],
            )
        )

    lines.extend(
        [
            "",
            "## Bootstrap Intervals",
            "",
            "| Method | Metric | Slice | Estimate | 95% Lower | 95% Upper |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for interval in report["case_bootstrap_intervals"] + report["hierarchical_bootstrap_intervals"]:
        lines.append(
            "| `{method}` | `{metric}` | `{dimension}={value}` | {estimate:.6f} | {lower:.6f} | {upper:.6f} |".format(
                method=interval["method"],
                metric=interval["metric_id"],
                dimension=interval["slice"]["dimension"],
                value=interval["slice"]["value"],
                estimate=interval["estimate"],
                lower=interval["lower"],
                upper=interval["upper"],
            )
        )

    lines.extend(
        [
            "",
            "## Deferred Analyses",
            "",
            f"- McNemar-style analysis: `{report['mcnemar_style_analysis']['status']}`",
            f"- Human/manual review: `{report['manual_review_status']['percent_complete']:.1f}%` complete",
            "",
            report["mcnemar_style_analysis"]["reason"],
            "",
            "## Next Dependencies",
            "",
        ]
    )
    for dependency in report["next_dependencies"]:
        lines.append(f"- {dependency}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inclusion-table", type=Path, default=DEFAULT_INCLUSION_TABLE)
    parser.add_argument("--descriptive-rates", type=Path, default=DEFAULT_DESCRIPTIVE_RATES)
    parser.add_argument("--paired-summary", type=Path, default=DEFAULT_PAIRED_SUMMARY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    inclusion_table_path = (
        args.inclusion_table if args.inclusion_table.is_absolute() else REPO_ROOT / args.inclusion_table
    )
    descriptive_rates_path = (
        args.descriptive_rates if args.descriptive_rates.is_absolute() else REPO_ROOT / args.descriptive_rates
    )
    paired_summary_path = (
        args.paired_summary if args.paired_summary.is_absolute() else REPO_ROOT / args.paired_summary
    )
    output_path = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    report = build_report(inclusion_table_path, descriptive_rates_path, paired_summary_path)
    write_json(output_path, report)
    write_markdown(output_path.with_suffix(".md"), report)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
