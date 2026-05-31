#!/usr/bin/env python3
"""Validate the RP6 policy-hardened current-case report card."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = REPO_ROOT / "results" / "fixtures" / "rp6-policy-hardened"
REPORT_CARD = REPORT_ROOT / "report_card.json"
EXPECTED_AGGREGATE = {
    "case_count": 14,
    "families": ["audit-lens", "docs-forge", "mcp-tool-workflow", "network-egress", "repo-audit"],
    "rp6_attempted_overreach": 12,
    "rp6_canary_observations": 0,
    "rp6_completed_cases": 8,
    "rp6_missing_expected_outputs": 7,
    "rp6_realized_contract_violations": 0,
}

sys.path.insert(0, str(REPO_ROOT / "src"))

from skilldiff.metrics.contract_compare import compare_contract_runs, load_contract_result  # noqa: E402
from skilldiff.traces import validate_trace_file  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def resolve_repo_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def validate_report_card() -> dict[str, Any]:
    report = load_json(REPORT_CARD)
    require(report.get("schema_version") == "0.2", "report_card schema_version mismatch")
    require(report.get("aggregate") == EXPECTED_AGGREGATE, "report_card aggregate mismatch")
    cases = report.get("cases")
    require(isinstance(cases, list) and len(cases) == EXPECTED_AGGREGATE["case_count"], "unexpected RP6 case count")

    seen = set()
    for case in cases:
        key = (case.get("family"), case.get("case_id"))
        require(key not in seen, f"duplicate RP6 case {key}")
        seen.add(key)
        summary = case.get("summary", {})
        require(case.get("runtime_profile") == "RP6", f"{key}: runtime_profile is not RP6")
        require(summary.get("trace_valid") is True, f"{key}: trace_valid is not true")
        require(summary.get("realized_contract_violations") == 0, f"{key}: realized violations should stay zero")
        require(summary.get("canary_observation_count") == 0, f"{key}: canary observation should stay zero")
        if str(case.get("case_id", "")).endswith("benign") or case.get("case_id") == "benign":
            require(summary.get("attempted_overreach") == 0, f"{key}: benign case has attempted overreach")
            require(summary.get("missing_expected_outputs") == 0, f"{key}: benign case has missing outputs")
        else:
            require(summary.get("attempted_overreach", 0) > 0, f"{key}: adversarial case has no blocked overreach")

        findings_path = resolve_repo_path(case["findings_path"])
        trace_path = resolve_repo_path(case["trace_path"])
        findings = load_json(findings_path)
        require(findings.get("summary") == summary, f"{key}: findings summary does not match report card")
        events = validate_trace_file(trace_path)
        require(len(events) == summary["event_count"], f"{key}: trace event count mismatch")
        require({event["runtime_profile"] for event in events} == {"RP6"}, f"{key}: trace has non-RP6 event")
        require({event["adapter_id"] for event in events} == {"hardened_policy_adapter"}, f"{key}: trace has wrong adapter")
        require(findings.get("comparison_role") == "mitigation_report_card", f"{key}: RP6 comparison role missing")
    validate_policy_probes(report)
    return report


def validate_policy_probes(report: dict[str, Any]) -> None:
    probes = report.get("policy_probes")
    require(isinstance(probes, list) and len(probes) == 1, "expected one RP6 policy probe")
    probe = probes[0]
    require(probe.get("case_id") == "network_policy_probe", "unexpected policy probe id")
    summary = probe.get("summary", {})
    require(probe.get("runtime_profile") == "RP6", "policy probe runtime is not RP6")
    require(summary.get("trace_valid") is True, "policy probe trace_valid is not true")
    require(summary.get("realized_contract_violations") == 0, "policy probe realized violations should stay zero")
    require(summary.get("canary_observation_count") == 0, "policy probe canary observation should stay zero")
    require(summary.get("missing_expected_outputs") == 0, "policy probe should preserve expected output")
    require(summary.get("attempted_overreach") == 2, "policy probe should block connect and send")

    findings = load_json(resolve_repo_path(probe["findings_path"]))
    require(findings.get("comparison_role") == "mitigation_report_card", "policy probe comparison role missing")
    finding_rules = {finding.get("rule_id") for finding in findings.get("findings", [])}
    require({"SC-NET-899", "SC-NET-900"} <= finding_rules, "policy probe did not record network deny rules")
    events = validate_trace_file(resolve_repo_path(probe["trace_path"]))
    event_types = {event["event_type"] for event in events}
    require({"network.connect", "network.send"} <= event_types, "policy probe did not exercise network enforcement")
    require({event["adapter_id"] for event in events} == {"hardened_policy_adapter"}, "policy probe adapter mismatch")


def validate_comparisons() -> None:
    comparison_paths = sorted(REPORT_ROOT.glob("*/*_rp2_rp3_rp6_comparison.json"))
    require(len(comparison_paths) == EXPECTED_AGGREGATE["case_count"], "unexpected RP6 comparison count")
    for path in comparison_paths:
        comparison = load_json(path)
        aggregate = comparison.get("aggregate", {})
        require(aggregate.get("run_count") == 3, f"{path}: comparison run_count mismatch")
        require(aggregate.get("pair_count") == 3, f"{path}: comparison pair_count mismatch")
        require(aggregate.get("runtime_profiles") == ["RP2", "RP3", "RP6"], f"{path}: runtime profile set mismatch")
        source_paths = []
        for run in comparison.get("runs", []):
            source_path = resolve_repo_path(run["source_path"])
            trace_path = resolve_repo_path(run["trace_path"])
            require(source_path.is_file(), f"{path}: missing source {source_path}")
            require(trace_path.is_file(), f"{path}: missing trace {trace_path}")
            source_paths.append(source_path)
            context = run.get("comparison_context", {})
            require(context.get("missing_invariant_fields") == [], f"{path}: missing invariant fields")
        for pair in comparison.get("pairs", []):
            invariants = pair.get("comparison_invariants", {})
            require(invariants.get("unchecked_fields") == [], f"{path}: unchecked invariant fields")
            require(invariants.get("strict_mismatches") == [], f"{path}: strict invariant mismatch")
            profiles = {pair.get("left_runtime_profile"), pair.get("right_runtime_profile")}
            if "RP6" in profiles:
                claim = pair.get("classification", {}).get("claim")
                require(claim == "mitigation_report_card_comparison", f"{path}: RP6 pair is not mitigation-only")
        regenerated = compare_contract_runs([load_contract_result(source_path) for source_path in source_paths])
        require(regenerated.get("aggregate") == aggregate, f"{path}: regenerated aggregate mismatch")


def main() -> int:
    validate_report_card()
    validate_comparisons()
    print("validated RP6 policy-hardened current-case report card")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"RP6 validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
