"""Markdown and JSON report writer for runtime report cards."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json


def runtime_report_card_texts(report: dict[str, Any]) -> tuple[str, str]:
    return json.dumps(report, indent=2, sort_keys=True) + "\n", render_markdown(report)


def write_runtime_report_card(report: dict[str, Any], output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    json_text, markdown_text = runtime_report_card_texts(report)
    output_json.write_text(json_text, encoding="utf-8")
    output_md.write_text(markdown_text, encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    aggregate = report["aggregate"]
    metrics = report["metrics"]
    evidence = report["evidence_coverage"]
    lines = [
        "# Runtime Report Card",
        "",
        f"- Runtime profile: `{report['runtime_profile']}`",
        f"- Generated at: `{report['generated_at']}`",
        f"- Boundary: {report['boundary']}",
        "",
        "## Summary",
        "",
        "| Runs | Benign | Adversarial | Unknown | Trace-valid | Pairwise comparisons | Expected pairwise comparisons |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        "| {runs} | {benign} | {adversarial} | {unknown} | {trace_valid} | {pairs} | {expected_pairs} |".format(
            runs=aggregate["run_count"],
            benign=aggregate["benign_run_count"],
            adversarial=aggregate["adversarial_run_count"],
            unknown=aggregate["unknown_role_run_count"],
            trace_valid=aggregate["trace_valid_runs"],
            pairs=aggregate["comparison_pair_count"],
            expected_pairs=aggregate["expected_comparison_pair_count"],
        ),
        "",
        "## Metrics",
        "",
        "| Metric | Value | Numerator | Denominator |",
        "| --- | ---: | ---: | ---: |",
    ]
    for label, metric_key in (
        ("Contract violation rate", "contract_violation_rate"),
        ("Attempted overreach rate", "attempted_overreach_rate"),
        ("Benign task success rate", "benign_task_success_rate"),
        ("Secure benign success rate", "secure_benign_success_rate"),
        ("Adversarial realized-violation rate", "adversarial_realized_violation_rate"),
        ("Utility cost rate", "utility_cost_rate"),
        ("Approval burden", "approval_burden"),
        ("Runtime risk score proxy", "runtime_risk_score_proxy"),
    ):
        metric = metrics[metric_key]
        lines.append(
            "| {label} | {value} | {numerator} | {denominator} |".format(
                label=label,
                value=_format_metric_value(metric),
                numerator=_format_scalar(metric.get("numerator")),
                denominator=_format_scalar(metric.get("denominator")),
            )
        )

    lines.extend(
        [
            "",
            "## Evidence Coverage",
            "",
            "| Metric | Value | Numerator | Denominator |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for label, metric_key in (
        ("Trace-valid rate", "trace_valid_rate"),
        ("Comparison-pair coverage rate", "comparison_pair_coverage_rate"),
        ("Instrumentation-failure run rate", "instrumentation_failure_run_rate"),
    ):
        metric = evidence[metric_key]
        lines.append(
            "| {label} | {value} | {numerator} | {denominator} |".format(
                label=label,
                value=_format_metric_value(metric),
                numerator=_format_scalar(metric.get("numerator")),
                denominator=_format_scalar(metric.get("denominator")),
            )
        )

    lines.extend(
        [
            "",
            "## Pairwise Disagreement",
            "",
            "| Counterpart | Pairs | Runtime-drift candidate pairs | Mitigation/report-card pairs | Disagreements | Disagreement rate |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for pair in report["pairwise"]:
        lines.append(
            "| `{counterpart}` | {pairs} | {runtime_drift} | {mitigation} | {disagreements} | {rate} |".format(
                counterpart=pair["counterpart_runtime_profile"],
                pairs=pair["pair_count"],
                runtime_drift=pair["runtime_drift_candidate_pairs"],
                mitigation=pair["mitigation_report_card_pairs"],
                disagreements=pair["pairwise_disagreements"],
                rate=_format_metric_value(pair["pairwise_disagreement_rate"]),
            )
        )
        drift_rates = pair["drift_class_pair_rates"]
        lines.append(
            "| drift classes | D1 {d1} | D2 {d2} | D3 {d3} | D4 {d4} | D5 {d5} |".format(
                d1=_format_metric_value(drift_rates["D1"]),
                d2=_format_metric_value(drift_rates["D2"]),
                d3=_format_metric_value(drift_rates["D3"]),
                d4=_format_metric_value(drift_rates["D4"]),
                d5=_format_metric_value(drift_rates["D5"]),
            )
        )

    lines.extend(_slice_table("By Category", report["breakdowns"]["by_category"]))
    lines.extend(_slice_table("By Attack Family", report["breakdowns"]["by_attack_family"]))
    lines.extend(
        [
            "## Artifact Inputs",
            "",
            f"- Findings JSON files: `{len(report['artifacts']['finding_paths'])}`",
            f"- Comparison JSON files: `{len(report['artifacts']['comparison_paths'])}`",
        ]
    )
    return "\n".join(lines) + "\n"


def _slice_table(title: str, rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "",
        f"## {title}",
        "",
        "| Slice | Runs | Realized violations | Attempted overreach | Functional success | Attack-success proxy | Missing outputs |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| `{label}` | {run_count} | {realized} | {attempted} | {functional} | {attack_success} | {missing} |".format(
                label=row["label"],
                run_count=row["run_count"],
                realized=row["realized_violation_runs"],
                attempted=row["attempted_overreach_runs"],
                functional=row["functional_success_runs"],
                attack_success=row["attack_success_proxy_runs"],
                missing=row["missing_output_runs"],
            )
        )
    if not rows:
        lines.append("| `none` | 0 | 0 | 0 | 0 | 0 | 0 |")
    return lines


def _format_metric_value(metric: dict[str, Any]) -> str:
    if not metric.get("supported", False):
        return "NA"
    value = metric.get("value")
    if value is None:
        return "NA"
    return f"{value:.4f}"


def _format_scalar(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)
