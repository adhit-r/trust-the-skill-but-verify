#!/usr/bin/env python3
"""Build/check source-mix RP6 repeat-stability aggregate evidence."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "benchmark" / "manifests" / "benchmark-cases-current.json"
REPORT_ROOT = REPO_ROOT / "results" / "fixtures" / "strengthening" / "source-mix-rp6-report-card"
OUT_ROOT = REPO_ROOT / "results" / "fixtures" / "strengthening" / "source-mix-rp6-repeat-stability"
OUT_JSON = OUT_ROOT / "repeat_stability.json"
OUT_MD = OUT_ROOT / "repeat_stability.md"
EXECUTION_LEVEL = "controlled_single_repeat_fixture_rp2_rp3"
SOURCE_LABELS = {"first_party", "public"}
REPEAT_IDS = (1, 2, 3)
CLAIM_BOUNDARY_FALSE_KEYS = (
    "completed_statistics_claimed",
    "reviewer_adjudication_claimed",
    "source_mix_completion_claimed",
    "prevalence_claim",
    "defense_success_claim",
    "live_product_claim",
    "commercial_runtime_claim",
    "public_network_claim",
    "runtime_drift_claim",
    "model_mediated_stability_claim",
)
SUMMARY_FIELDS = (
    "realized_contract_violations",
    "attempted_overreach",
    "missing_expected_outputs",
    "output_oracle_failures",
    "canary_observation_count",
)


def load_json(path: Path) -> Any:
    if not path.is_file():
        raise FileNotFoundError(f"missing {repo_path(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def resolve_repo_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def report_card_path(repeat_id: int) -> Path:
    name = "report_card.json" if repeat_id == 1 else f"report_card_repeat{repeat_id}.json"
    return REPORT_ROOT / name


def source_mix_cases() -> list[dict[str, Any]]:
    manifest = load_json(MANIFEST_PATH)
    cases = [
        case
        for case in manifest.get("cases", [])
        if case.get("execution", {}).get("execution_level") == EXECUTION_LEVEL
        and case.get("provenance", {}).get("source_mix", {}).get("label") in SOURCE_LABELS
    ]
    return sorted(cases, key=lambda case: case["case_id"])


def summary_without_event_count(summary: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in summary.items() if key != "event_count"}


def stable(values: list[dict[str, Any]]) -> bool:
    rendered = {json.dumps(value, sort_keys=True) for value in values}
    return len(rendered) == 1


def load_repeat_card(repeat_id: int, expected_ids: set[str]) -> dict[str, dict[str, Any]]:
    report = load_json(report_card_path(repeat_id))
    require(report.get("schema_version") == "0.1", f"repeat {repeat_id}: schema_version mismatch")
    require(report.get("report_type") == "source_mix_rp6_report_card", f"repeat {repeat_id}: report type mismatch")
    boundary = str(report.get("boundary") or "")
    for phrase in (
        "Broader RP6 profile-backed report-card evidence",
        "not live product behavior",
        "source-mix completion",
        "defense success",
        "commercial-runtime behavior",
        "public-network behavior",
        "prevalence evidence",
        "human adjudication evidence",
    ):
        require(phrase in boundary, f"repeat {repeat_id}: boundary missing {phrase!r}")
    aggregate = report.get("aggregate", {})
    require(aggregate.get("repeat_ids") == [repeat_id], f"repeat {repeat_id}: repeat_ids mismatch")
    rows = report.get("cases")
    require(isinstance(rows, list), f"repeat {repeat_id}: cases must be a list")
    observed_ids = {str(row.get("case_id")) for row in rows}
    require(observed_ids == expected_ids, f"repeat {repeat_id}: case IDs do not match manifest")
    by_case: dict[str, dict[str, Any]] = {}
    for row in rows:
        case_id = str(row["case_id"])
        require(row.get("repeat_id") == repeat_id, f"{case_id}: repeat_id mismatch")
        require(row.get("runtime_profile") == "RP6", f"{case_id}: runtime profile mismatch")
        require(row.get("adapter_outcome") == "completed", f"{case_id}: adapter outcome mismatch")
        require(row.get("exit_code") == 0, f"{case_id}: exit code mismatch")
        require(row.get("source_mix_label") in SOURCE_LABELS, f"{case_id}: invalid source mix")
        summary = row.get("summary", {})
        require(summary.get("trace_valid") is True, f"{case_id}: trace is not valid")
        findings_path = resolve_repo_path(row["findings_path"])
        trace_path = resolve_repo_path(row["trace_path"])
        findings = load_json(findings_path)
        require(trace_path.is_file(), f"{case_id}: missing trace {repo_path(trace_path)}")
        require(findings.get("summary") == summary, f"{case_id}: stale findings summary")
        require(findings.get("comparison_role") == "mitigation_report_card", f"{case_id}: missing comparison role")
        require(findings.get("evidence_scope") == "source_mix_rp6_report_card_fixture", f"{case_id}: scope mismatch")
        by_case[case_id] = row
    return by_case


def build_report() -> dict[str, Any]:
    manifest_cases = source_mix_cases()
    expected_ids = {case["case_id"] for case in manifest_cases}
    manifest_by_id = {case["case_id"]: case for case in manifest_cases}
    cards = {repeat_id: load_repeat_card(repeat_id, expected_ids) for repeat_id in REPEAT_IDS}
    rows: list[dict[str, Any]] = []

    for case_id in sorted(expected_ids):
        observations = []
        for repeat_id in REPEAT_IDS:
            row = cards[repeat_id][case_id]
            findings = load_json(resolve_repo_path(row["findings_path"]))
            observations.append(
                {
                    "adapter_outcome": row["adapter_outcome"],
                    "exit_code": row["exit_code"],
                    "findings_path": row["findings_path"],
                    "repeat_id": repeat_id,
                    "run_id": findings.get("run_id"),
                    "summary": row["summary"],
                    "summary_without_event_count": summary_without_event_count(row["summary"]),
                    "trace_path": row["trace_path"],
                }
            )
        summaries = [observation["summary"] for observation in observations]
        summaries_without_events = [observation["summary_without_event_count"] for observation in observations]
        case = manifest_by_id[case_id]
        rows.append(
            {
                "case_id": case_id,
                "category": case["category"],
                "family": case["family_id"],
                "observation_count": len(observations),
                "observations": observations,
                "repeat_ids": list(REPEAT_IDS),
                "source_mix_label": case["provenance"]["source_mix"]["label"],
                "stable_summary_excluding_event_count": stable(summaries_without_events),
                "stable_summary_including_event_count": stable(summaries),
                "task_id": case["provenance"]["task_id"],
            }
        )

    source_counts = Counter(row["source_mix_label"] for row in rows)
    aggregate = {
        "case_count": len(rows),
        "deterministic_stability_claims_supported": sum(
            1 for row in rows if row["stable_summary_excluding_event_count"]
        ),
        "families": sorted({row["family"] for row in rows}),
        "family_count": len({row["family"] for row in rows}),
        "minimum_repeats_for_deterministic_stability_claim": len(REPEAT_IDS),
        "repeat_ids": list(REPEAT_IDS),
        "repeat_observation_count": len(rows) * len(REPEAT_IDS),
        "repeats_per_case": len(REPEAT_IDS),
        "rp6_attempted_overreach": sum(
            observation["summary"]["attempted_overreach"] for row in rows for observation in row["observations"]
        ),
        "rp6_canary_observations": sum(
            observation["summary"]["canary_observation_count"]
            for row in rows
            for observation in row["observations"]
        ),
        "rp6_missing_expected_outputs": sum(
            observation["summary"]["missing_expected_outputs"]
            for row in rows
            for observation in row["observations"]
        ),
        "rp6_output_oracle_failures": sum(
            observation["summary"]["output_oracle_failures"]
            for row in rows
            for observation in row["observations"]
        ),
        "rp6_realized_contract_violations": sum(
            observation["summary"]["realized_contract_violations"]
            for row in rows
            for observation in row["observations"]
        ),
        "source_mix_counts": dict(sorted(source_counts.items())),
        "stable_summary_excluding_event_count": sum(
            1 for row in rows if row["stable_summary_excluding_event_count"]
        ),
        "stable_summary_including_event_count": sum(
            1 for row in rows if row["stable_summary_including_event_count"]
        ),
        "statistical_repeat_stability_claims_supported": 0,
        "trace_valid_count": sum(
            1
            for row in rows
            for observation in row["observations"]
            if observation["summary"].get("trace_valid") is True
        ),
    }
    report = {
        "schema_version": "0.1",
        "report_type": "source_mix_rp6_repeat_stability",
        "boundary": (
            "Bounded deterministic repeat-stability evidence for first-party/public source-mix RP6 "
            "report-card fixtures across repeat IDs 1, 2, and 3. This is not source-mix completion, "
            "live product behavior, defense success, commercial-runtime behavior, public-network behavior, "
            "runtime-drift evidence, prevalence evidence, statistical stability, model-mediated stability, "
            "or human adjudication evidence."
        ),
        "claim_boundary": {key: False for key in CLAIM_BOUNDARY_FALSE_KEYS},
        "aggregate": aggregate,
        "cases": rows,
    }
    return report


def build_markdown(report: dict[str, Any]) -> str:
    aggregate = report["aggregate"]
    lines = [
        "# Source-Mix RP6 Repeat Stability",
        "",
        report["boundary"],
        "",
        "## Aggregate",
        "",
        f"- Cases: `{aggregate['case_count']}`",
        f"- Families: `{aggregate['family_count']}`",
        f"- Repeat IDs: `{aggregate['repeat_ids']}`",
        f"- Repeat observations: `{aggregate['repeat_observation_count']}`",
        f"- Trace-valid observations: `{aggregate['trace_valid_count']}`",
        f"- Source mix: `{aggregate['source_mix_counts']}`",
        f"- Stable summaries excluding event count: `{aggregate['stable_summary_excluding_event_count']}`",
        f"- Statistical repeat-stability claims supported: `{aggregate['statistical_repeat_stability_claims_supported']}`",
        "",
        "| Family | Task | Source Mix | Stable Excluding Event Count | Observations |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for row in report["cases"]:
        lines.append(
            "| {family} | `{task}` | {source_mix} | {stable} | {count} |".format(
                family=row["family"],
                task=row["task_id"],
                source_mix=row["source_mix_label"],
                stable="yes" if row["stable_summary_excluding_event_count"] else "no",
                count=row["observation_count"],
            )
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if tracked output is stale.")
    args = parser.parse_args(argv)

    report = build_report()
    markdown = build_markdown(report)
    if args.check:
        current_json = load_json(OUT_JSON)
        require(current_json == report, f"{repo_path(OUT_JSON)} is stale")
        current_markdown = OUT_MD.read_text(encoding="utf-8")
        require(current_markdown == markdown, f"{repo_path(OUT_MD)} is stale")
        print(
            "validated source-mix RP6 repeat stability: "
            f"{report['aggregate']['case_count']} cases, "
            f"{report['aggregate']['repeat_observation_count']} observations"
        )
        return 0

    write_json(OUT_JSON, report)
    OUT_MD.write_text(markdown, encoding="utf-8")
    print(
        "wrote source-mix RP6 repeat stability: "
        f"{report['aggregate']['case_count']} cases, "
        f"{report['aggregate']['repeat_observation_count']} observations"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"source-mix RP6 repeat-stability build failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
