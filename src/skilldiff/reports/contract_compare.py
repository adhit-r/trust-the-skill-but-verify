"""Markdown and JSON report writer for contract-run comparisons."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json


def write_comparison_report(report: dict[str, Any], output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Contract Run Comparison",
        "",
        "## Summary",
        "",
        "| Runs | Pairs | Runtime Profiles | Contracts | Pairwise Disagreements | Runtime Drift Claims |",
        "| ---: | ---: | --- | --- | ---: | ---: |",
        "| {runs} | {pairs} | `{profiles}` | `{contracts}` | {disagreements} | {claims} |".format(
            runs=report["aggregate"]["run_count"],
            pairs=report["aggregate"]["pair_count"],
            profiles=", ".join(report["aggregate"]["runtime_profiles"]) or "none",
            contracts=", ".join(report["aggregate"]["contract_ids"]) or "none",
            disagreements=report["aggregate"]["pairwise_disagreements"],
            claims=report["aggregate"]["runtime_drift_claims"],
        ),
        "",
        "## Per-Run Counts",
        "",
        "| Run | Runtime | Skill | Task | Contract | Events | Findings | Realized Violations | Attempted Overreach | Canary Observations | Drift Classes |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for run in report["runs"]:
        context = run.get("comparison_context", {})
        lines.append(
            "| `{run}` | `{runtime}` | `{skill}` | `{task}` | `{contract}` | {events} | {findings} | {violations} | {overreach} | {canaries} | `{classes}` |".format(
                run=run["run_id"],
                runtime=run["runtime_profile"],
                skill=context.get("skill_id") or "unknown",
                task=context.get("task_id") or "unknown",
                contract=run["contract_id"],
                events=run["summary"]["event_count"],
                findings=run["finding_count"],
                violations=run["summary"]["realized_contract_violations"],
                overreach=run["summary"]["attempted_overreach"],
                canaries=run["summary"]["canary_observation_count"],
                classes=", ".join(run["drift_classes_observed"]) or "none",
            )
        )
    lines.extend(["", "## Pairwise Disagreements", ""])
    for pair in report["pairs"]:
        lines.extend(
            [
                "### `{left}` vs `{right}`".format(left=pair["left_run_id"], right=pair["right_run_id"]),
                "",
                f"- Runtime profiles: `{pair['left_runtime_profile']}` vs `{pair['right_runtime_profile']}`",
                f"- Classification: `{pair['classification']['claim']}`",
                f"- Boundary: {pair['classification']['boundary']}",
                f"- Unchecked planned invariants: `{', '.join(pair.get('comparison_invariants', {}).get('unchecked_fields', [])) or 'none'}`",
                f"- Shared findings: `{pair['shared_finding_count']}`",
                f"- Disagreements: `{pair['disagreement_count']}`",
                "- Summary delta (right minus left): realized violations `{violations}`, attempted overreach `{overreach}`, canary observations `{canaries}`, events `{events}`".format(
                    violations=pair["summary_delta"]["realized_contract_violations"],
                    overreach=pair["summary_delta"]["attempted_overreach"],
                    canaries=pair["summary_delta"]["canary_observation_count"],
                    events=pair["summary_delta"]["event_count"],
                ),
                "",
            ]
        )
        lines.extend(_finding_block("Only in left", pair["only_in_left"]))
        lines.extend(_finding_block("Only in right", pair["only_in_right"]))
    lines.extend(
        [
            "## Boundary",
            "",
            "This utility compares existing contract-check outputs. It can identify pairwise disagreement in observed findings, but it does not prove runtime-induced drift unless the compared runs are the same skill-task, fixtures, and prompt variant under different runtime profiles.",
        ]
    )
    return "\n".join(lines) + "\n"


def _finding_block(title: str, findings: list[dict[str, Any]]) -> list[str]:
    lines = [f"#### {title}", ""]
    if not findings:
        return lines + ["None.", ""]
    for finding in findings:
        lines.append(
            "- `{event_type}` `{target}` rule `{rule}` severity `{severity}` drift `{classes}`".format(
                event_type=finding.get("event_type") or "unknown",
                target=finding.get("target") or "unknown",
                rule=finding.get("rule_id") or "unknown",
                severity=finding.get("severity") or "unknown",
                classes=", ".join(finding.get("drift_classes") or []) or "none",
            )
        )
    lines.append("")
    return lines
