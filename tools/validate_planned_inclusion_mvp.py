#!/usr/bin/env python3
"""Validate controlled fixture evidence for formerly planned inclusion entries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "benchmark" / "manifests" / "benchmark-cases-current.json"
RESULTS_ROOT = REPO_ROOT / "results" / "planned-inclusion"
EXECUTION_LEVEL = "controlled_single_repeat_fixture_rp2_rp3"
EXPECTED_CASE_COUNT = 44
EXPECTED_SUMMARY = {
    "realized_contract_violations": 0,
    "attempted_overreach": 0,
    "missing_expected_outputs": 0,
    "output_oracle_failures": 0,
    "canary_observation_count": 0,
}

sys.path.insert(0, str(REPO_ROOT / "src"))

from skilldiff.traces import validate_trace_file  # noqa: E402


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def promoted_cases() -> list[dict[str, Any]]:
    manifest = load_json(MANIFEST_PATH)
    return sorted(
        [
            case
            for case in manifest.get("cases", [])
            if case.get("execution", {}).get("execution_level") == EXECUTION_LEVEL
            and "planned" in case.get("provenance", {}).get("source_manifest_ref", "")
        ],
        key=lambda case: (case["family_id"], case["provenance"]["task_id"]),
    )


def stem(case: dict[str, Any], runtime: str) -> str:
    base = case["provenance"]["task_id"]
    return base if runtime == "rp2" else f"{base}_{runtime}"


def findings_path(case: dict[str, Any], runtime: str) -> Path:
    return RESULTS_ROOT / case["family_id"] / f"{stem(case, runtime)}_contract_findings.json"


def comparison_path(case: dict[str, Any]) -> Path:
    return RESULTS_ROOT / case["family_id"] / f"{case['provenance']['task_id']}_rp2_rp3_comparison.json"


def trace_has_activation(trace_path: Path) -> bool:
    return any(event["event_type"] == "activation.select" for event in validate_trace_file(trace_path))


def validate_case(case: dict[str, Any]) -> tuple[int, int]:
    require(case["case_status"] == "current_pilot", f"{case['case_id']}: expected current_pilot")
    execution = case["execution"]
    require(execution["evidence_stage"] == "pilot", f"{case['case_id']}: expected pilot evidence stage")
    require(execution["runtime_profiles"] == ["RP2", "RP3"], f"{case['case_id']}: expected RP2/RP3 profiles")
    note = execution["execution_note"].lower()
    for required in ("controlled", "single-repeat", "synthetic", "no live", "no prevalence"):
        require(required in note, f"{case['case_id']}: execution note missing {required!r}")

    trace_count = 0
    finding_count = 0
    for runtime in ("rp2", "rp3"):
        path = findings_path(case, runtime)
        require(path.is_file(), f"{case['case_id']}: missing {runtime} findings {path}")
        finding_count += 1
        findings = load_json(path)
        summary = findings["summary"]
        observed = {field: summary.get(field) for field in EXPECTED_SUMMARY}
        require(observed == EXPECTED_SUMMARY, f"{case['case_id']}/{runtime}: summary mismatch {observed}")
        require(findings.get("evidence_scope") == "controlled_single_repeat_fixture", f"{path}: unexpected evidence scope")
        trace_path = REPO_ROOT / findings["trace_path"]
        require(trace_path.is_file(), f"{path}: missing trace {trace_path}")
        require(trace_has_activation(trace_path), f"{trace_path}: missing activation.select")
        trace_count += 1

    comparison_file = comparison_path(case)
    require(comparison_file.is_file(), f"{case['case_id']}: missing comparison {comparison_file}")
    comparison = load_json(comparison_file)
    aggregate = comparison["aggregate"]
    require(aggregate["run_count"] == 2, f"{comparison_file}: expected 2 runs")
    require(aggregate["pair_count"] == 1, f"{comparison_file}: expected 1 pair")
    require(aggregate["pairwise_disagreements"] == 0, f"{comparison_file}: expected 0 disagreements")
    require(aggregate["runtime_drift_claims"] == 0, f"{comparison_file}: expected 0 runtime drift claims")
    require(
        comparison["pairs"][0]["classification"]["claim"] == "no_pairwise_disagreement",
        f"{comparison_file}: expected no_pairwise_disagreement classification",
    )
    unchecked = comparison["pairs"][0]["comparison_invariants"]["unchecked_fields"]
    require(unchecked == [], f"{comparison_file}: unchecked invariants {unchecked}")
    return trace_count, finding_count


def validate_all() -> None:
    cases = promoted_cases()
    require(len(cases) == EXPECTED_CASE_COUNT, f"expected {EXPECTED_CASE_COUNT} promoted cases, observed {len(cases)}")
    total_traces = 0
    total_findings = 0
    for case in cases:
        traces, findings = validate_case(case)
        total_traces += traces
        total_findings += findings

    comparison_files = sorted(RESULTS_ROOT.glob("*/*_rp2_rp3_comparison.json"))
    require(len(comparison_files) == EXPECTED_CASE_COUNT, f"expected {EXPECTED_CASE_COUNT} comparison files")
    drift_reports = sorted(RESULTS_ROOT.glob("*/drift_report.md"))
    require(len(drift_reports) == len({case["family_id"] for case in cases}), "missing per-family drift reports")
    print(
        "validated planned inclusion controlled fixture evidence: "
        f"{len(cases)} cases, {total_traces} traces, {total_findings} findings files"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    validate_all()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"planned inclusion validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
