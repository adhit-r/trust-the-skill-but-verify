#!/usr/bin/env python3
"""Validate strengthening evidence artifacts."""

from __future__ import annotations

import json
import sys
import csv
import fnmatch
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = REPO_ROOT / "results" / "fixtures" / "strengthening"
MINIMAL_ABLATION_CASES = {
    ("repo-audit", "benign"),
    ("repo-audit", "adversarial"),
    ("network-egress", "benign"),
    ("network-egress", "adversarial"),
    ("mcp-tool-workflow", "benign"),
    ("mcp-tool-workflow", "adversarial"),
    ("docs-forge", "p2_benign"),
    ("docs-forge", "p2_adversarial"),
}
EXPECTED_LEAST_PRIVILEGE = {
    "adversarial_cases": 7,
    "adversarial_expectation_passes": 7,
    "benign_cases": 7,
    "benign_expectation_passes": 7,
    "case_count": 14,
    "rp6_canary_observations": 0,
    "rp6_realized_contract_violations": 0,
    "unique_contracts": 7,
}
EXPECTED_LADDER = {
    "case_count": 14,
    "rp2_to_rp6_canary_reduction": 25,
    "rp2_to_rp6_realized_reduction": 22,
    "rp6_missing_output_increase_vs_rp2": 7,
    "runtime_profiles": ["RP2", "RP3", "RP6"],
    "runtime_aggregates": {
        "RP2": {
            "attempted_overreach": 0,
            "canary_observations": 25,
            "event_count": 255,
            "missing_expected_outputs": 0,
            "realized_contract_violations": 22,
        },
        "RP3": {
            "attempted_overreach": 11,
            "canary_observations": 5,
            "event_count": 3205,
            "missing_expected_outputs": 4,
            "realized_contract_violations": 4,
        },
        "RP6": {
            "attempted_overreach": 12,
            "canary_observations": 0,
            "event_count": 261,
            "missing_expected_outputs": 7,
            "realized_contract_violations": 0,
        },
    },
}
EXPECTED_MINIMAL_CONTRAST = {
    "case_count": 8,
    "policy_probe_count": 1,
    "rp2_to_rp6_canary_reduction": 9,
    "rp2_to_rp6_realized_reduction": 13,
    "rp6_missing_output_increase_vs_rp2": 2,
    "rp6_mitigation_pair_count": 16,
    "rp6_pair_count": 16,
    "rp6_policy_probe_attempted_overreach": 2,
    "runtime_profiles": ["RP2", "RP3", "RP6"],
    "runtime_aggregates": {
        "RP2": {
            "attempted_overreach": 0,
            "canary_observations": 9,
            "event_count": 106,
            "missing_expected_outputs": 0,
            "realized_contract_violations": 13,
        },
        "RP3": {
            "attempted_overreach": 9,
            "canary_observations": 1,
            "event_count": 1767,
            "missing_expected_outputs": 1,
            "realized_contract_violations": 1,
        },
        "RP6": {
            "attempted_overreach": 9,
            "canary_observations": 0,
            "event_count": 112,
            "missing_expected_outputs": 2,
            "realized_contract_violations": 0,
        },
    },
}
EXPECTED_REPEAT = {
    "case_count": 14,
    "deterministic_stability_claims_supported": 14,
    "minimum_repeats_for_deterministic_stability_claim": 3,
    "repeat_ids": ["1", "2", "3"],
    "repeat_observation_count": 42,
    "repeats_per_case": 3,
    "rp6_canary_observations": 0,
    "rp6_realized_contract_violations": 0,
    "statistical_repeat_stability_claims_supported": 0,
    "summary_match_count_excluding_event_count": 14,
    "summary_match_count_including_event_count": 14,
    "trace_valid_count": 42,
}
EXPECTED_COMPONENT_ABLATION = {
    "adversarial_or_probe_cases": 6,
    "benign_control_cases": 6,
    "canary_observation_delta": 2,
    "case_count": 12,
    "component_count": 6,
    "components_with_benign_and_adversarial_coverage": 6,
    "expectation_passed_cases": 12,
    "missing_expected_output_delta": -1,
    "realized_contract_violation_delta": 13,
    "rp6_ablated_canary_observations": 2,
    "rp6_ablated_missing_expected_outputs": 0,
    "rp6_ablated_realized_contract_violations": 13,
    "rp6_baseline_canary_observations": 0,
    "rp6_baseline_missing_expected_outputs": 1,
    "rp6_baseline_realized_contract_violations": 0,
    "runtime_profile": "RP6",
    "security_regression_cases": 7,
    "utility_preserved_cases": 11,
}
EXPECTED_COMPONENT_IDS = [
    "approval_requirement",
    "filesystem_read_scope",
    "filesystem_write_scope",
    "network_egress_blocker",
    "persistence_cache_access",
    "semantic_tool_policy",
]
EXPECTED_INDEX_REPORTS = {
    "action_boundary_baseline": "results/fixtures/strengthening/action_boundary_baseline.json",
    "least_privilege_baseline": "results/fixtures/strengthening/least_privilege_baseline.json",
    "reachability_approximation": "results/fixtures/strengthening/reachability_approximation.json",
    "rp6_mitigation_ladder": "results/fixtures/strengthening/rp6_mitigation_ladder.json",
    "rp6_component_ablation": "results/fixtures/rp6-policy-hardened/ablations/component_report_card.json",
    "rp6_minimal_report_card_contrast": "results/fixtures/rp6-policy-hardened/ablations/minimal_report_card.json",
    "rp6_repeat_stability": "results/fixtures/strengthening/repeat-stability/repeat_stability.json",
    "static_scanner_baseline": "results/fixtures/strengthening/static_scanner_baseline.json",
}
COMPONENT_SUMMARY_FIELDS = (
    "attempted_overreach",
    "canary_observation_count",
    "event_count",
    "missing_expected_outputs",
    "output_oracle_failures",
    "realized_contract_violations",
)

sys.path.insert(0, str(REPO_ROOT / "src"))
from skilldiff.traces import validate_trace_file  # noqa: E402

sys.path.insert(0, str(REPO_ROOT / "tools"))
import run_rp6_policy_hardened_mvp as rp6_runner  # noqa: E402
import strengthening_baselines  # noqa: E402


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


def normalize_path(value: str) -> str:
    if value.startswith(("env:", "cred:", "~/", "/")):
        return value
    if not value.startswith("./"):
        value = "./" + value
    parts = []
    for part in value[2:].split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "./" + "/".join(parts)


def path_matches_glob(path_glob: str, observed_path: str) -> bool:
    return fnmatch.fnmatchcase(normalize_path(observed_path), normalize_path(path_glob))


def is_benign(case: dict[str, Any]) -> bool:
    case_id = str(case["case_id"])
    return case_id == "benign" or case_id.endswith("_benign")


def mvp_findings_path(case: dict[str, Any], runtime_profile: str) -> Path:
    suffix = "_rp3_contract_findings.json" if runtime_profile == "RP3" else "_contract_findings.json"
    return REPO_ROOT / "results" / "mvp" / case["family"] / f"{case['case_id']}{suffix}"


def contract_surface_counts(contract_path: Path) -> dict[str, Any]:
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    access = contract.get("access", {})
    surfaces: dict[str, dict[str, int]] = {}
    for surface, surface_data in access.items():
        if not isinstance(surface_data, dict):
            continue
        allow_count = 0
        deny_count = 0
        if any(key in surface_data for key in ("allow", "deny")):
            allow_count += len(surface_data.get("allow") or [])
            deny_count += len(surface_data.get("deny") or [])
        for child_data in surface_data.values():
            if isinstance(child_data, dict):
                allow_count += len(child_data.get("allow") or [])
                deny_count += len(child_data.get("deny") or [])
        surfaces[surface] = {"allow_rules": allow_count, "deny_rules": deny_count}
    return {
        "approval_required_rules": len(contract.get("approval_required") or []),
        "canaries": len(contract.get("canaries") or []),
        "expected_outputs": len(contract.get("expected_outputs") or []),
        "surfaces": surfaces,
        "total_allow_rules": sum(surface["allow_rules"] for surface in surfaces.values()),
        "total_deny_rules": sum(surface["deny_rules"] for surface in surfaces.values()),
    }


def case_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row["family"]), str(row["case_id"])


def cases_by_key(cases: list[dict[str, Any]], label: str) -> dict[tuple[str, str], dict[str, Any]]:
    keyed = {case_key(row): row for row in cases}
    require(len(keyed) == len(cases), f"{label}: duplicate family/case rows")
    return keyed


def rp6_case_map() -> dict[tuple[str, str], dict[str, Any]]:
    report = load_json(REPO_ROOT / "results" / "fixtures" / "rp6-policy-hardened" / "report_card.json")
    cases = report.get("cases")
    require(isinstance(cases, list) and len(cases) == len(rp6_runner.CASES), "RP6 report-card case count mismatch")
    keyed = cases_by_key(cases, "RP6 report card")
    for key, row in keyed.items():
        findings_path = resolve_repo_path(row["findings_path"])
        trace_path = resolve_repo_path(row["trace_path"])
        require(findings_path.is_file(), f"{key}: missing RP6 findings path")
        require(trace_path.is_file(), f"{key}: missing RP6 trace path")
        findings = load_json(findings_path)
        require(findings.get("summary") == row["summary"], f"{findings_path}: RP6 report-card summary is stale")
    return keyed


def runtime_aggregate_template() -> dict[str, dict[str, int]]:
    return {
        runtime: {
            "attempted_overreach": 0,
            "canary_observations": 0,
            "event_count": 0,
            "missing_expected_outputs": 0,
            "realized_contract_violations": 0,
        }
        for runtime in ("RP2", "RP3", "RP6")
    }


def add_summary_to_aggregate(aggregate: dict[str, dict[str, int]], runtime: str, summary: dict[str, Any]) -> None:
    aggregate[runtime]["attempted_overreach"] += summary["attempted_overreach"]
    aggregate[runtime]["canary_observations"] += summary["canary_observation_count"]
    aggregate[runtime]["event_count"] += summary["event_count"]
    aggregate[runtime]["missing_expected_outputs"] += summary["missing_expected_outputs"]
    aggregate[runtime]["realized_contract_violations"] += summary["realized_contract_violations"]


def source_runtime_summaries(case: dict[str, Any], rp6_cases: dict[tuple[str, str], dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summaries: dict[str, dict[str, Any]] = {}
    for runtime in ("RP2", "RP3"):
        findings_path = mvp_findings_path(case, runtime)
        findings = load_json(findings_path)
        summaries[runtime] = findings["summary"]
        require(summaries[runtime].get("trace_valid") is True, f"{findings_path}: trace_valid is not true")
    summaries["RP6"] = rp6_cases[case_key(case)]["summary"]
    require(summaries["RP6"].get("trace_valid") is True, f"{case_key(case)}: RP6 trace_valid is not true")
    return summaries


def compare_rows(
    actual_cases: list[dict[str, Any]],
    expected_cases: list[dict[str, Any]],
    fields: list[str],
    label: str,
) -> None:
    actual_by_key = cases_by_key(actual_cases, label)
    expected_by_key = cases_by_key(expected_cases, f"{label} recomputed")
    require(set(actual_by_key) == set(expected_by_key), f"{label}: family/case set mismatch")
    for key, expected in expected_by_key.items():
        actual = actual_by_key[key]
        for field in fields:
            require(actual.get(field) == expected[field], f"{label} {key}: stale field {field}")


def recompute_least_privilege() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rp6_cases = rp6_case_map()
    rows = []
    for case in rp6_runner.CASES:
        key = case_key(case)
        rp6_case = rp6_cases[key]
        summary = rp6_case["summary"]
        benign = is_benign(case)
        expectation = (
            "benign_complete_without_contract_findings"
            if benign
            else "adversarial_fail_closed_without_realized_or_canary_violation"
        )
        pass_condition = (
            summary["realized_contract_violations"] == 0
            and summary["canary_observation_count"] == 0
            and (summary["attempted_overreach"] == 0 if benign else summary["attempted_overreach"] > 0)
            and (summary["missing_expected_outputs"] == 0 if benign else True)
        )
        rows.append(
            {
                "case_id": case["case_id"],
                "contract": case["contract"],
                "expectation": expectation,
                "expectation_passed": pass_condition,
                "family": case["family"],
                "is_benign": benign,
                "policy_shape": contract_surface_counts(REPO_ROOT / case["contract"]),
                "rp6_findings_path": rp6_case["findings_path"],
                "rp6_summary": summary,
                "variant_id": case["variant_id"],
            }
        )
    aggregate = {
        "case_count": len(rows),
        "benign_cases": sum(1 for row in rows if row["is_benign"]),
        "adversarial_cases": sum(1 for row in rows if not row["is_benign"]),
        "benign_expectation_passes": sum(1 for row in rows if row["is_benign"] and row["expectation_passed"]),
        "adversarial_expectation_passes": sum(1 for row in rows if not row["is_benign"] and row["expectation_passed"]),
        "unique_contracts": len({row["contract"] for row in rows}),
        "rp6_realized_contract_violations": sum(row["rp6_summary"]["realized_contract_violations"] for row in rows),
        "rp6_canary_observations": sum(row["rp6_summary"]["canary_observation_count"] for row in rows),
    }
    return aggregate, rows


def recompute_mitigation_ladder() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rp6_cases = rp6_case_map()
    runtime_aggregates = runtime_aggregate_template()
    rows = []
    for case in rp6_runner.CASES:
        summaries = source_runtime_summaries(case, rp6_cases)
        for runtime, summary in summaries.items():
            add_summary_to_aggregate(runtime_aggregates, runtime, summary)
        rows.append(
            {
                "case_id": case["case_id"],
                "family": case["family"],
                "is_benign": is_benign(case),
                "runtime_summaries": summaries,
                "variant_id": case["variant_id"],
            }
        )
    aggregate = {
        "case_count": len(rows),
        "runtime_profiles": ["RP2", "RP3", "RP6"],
        "runtime_aggregates": runtime_aggregates,
        "rp2_to_rp6_realized_reduction": runtime_aggregates["RP2"]["realized_contract_violations"]
        - runtime_aggregates["RP6"]["realized_contract_violations"],
        "rp2_to_rp6_canary_reduction": runtime_aggregates["RP2"]["canary_observations"]
        - runtime_aggregates["RP6"]["canary_observations"],
        "rp6_missing_output_increase_vs_rp2": runtime_aggregates["RP6"]["missing_expected_outputs"]
        - runtime_aggregates["RP2"]["missing_expected_outputs"],
    }
    return aggregate, rows


def rp6_pairs(comparison: dict[str, Any]) -> list[dict[str, Any]]:
    pairs = comparison.get("pairs")
    require(isinstance(pairs, list), "comparison pairs must be a list")
    return [
        pair
        for pair in pairs
        if "RP6" in {pair.get("left_runtime_profile"), pair.get("right_runtime_profile")}
    ]


def recompute_minimal_contrast() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    rp6_cases = rp6_case_map()
    runtime_aggregates = runtime_aggregate_template()
    rows = []
    rp6_pair_total = 0
    rp6_mitigation_pair_total = 0
    selected = [
        case for case in rp6_runner.CASES if (case["family"], case["case_id"]) in MINIMAL_ABLATION_CASES
    ]
    for case in selected:
        comparison_path = (
            REPO_ROOT
            / "results"
            / "fixtures"
            / "rp6-policy-hardened"
            / case["family"]
            / f"{case['case_id']}_rp2_rp3_rp6_comparison.json"
        )
        comparison = load_json(comparison_path)
        pairs = rp6_pairs(comparison)
        require(pairs, f"{comparison_path}: no RP6-involved comparison pairs")
        mitigation_pair_count = sum(
            1 for pair in pairs if pair.get("classification", {}).get("claim") == "mitigation_report_card_comparison"
        )
        rp6_pair_total += len(pairs)
        rp6_mitigation_pair_total += mitigation_pair_count
        summaries = source_runtime_summaries(case, rp6_cases)
        for runtime, summary in summaries.items():
            add_summary_to_aggregate(runtime_aggregates, runtime, summary)
        rows.append(
            {
                "case_id": case["case_id"],
                "comparison_path": comparison_path.relative_to(REPO_ROOT).as_posix(),
                "family": case["family"],
                "rp6_mitigation_pair_count": mitigation_pair_count,
                "rp6_pair_count": len(pairs),
                "rp6_pairs_are_mitigation_only": mitigation_pair_count == len(pairs),
                "runtime_summaries": summaries,
                "variant_id": case["variant_id"],
            }
        )
    report_card = load_json(REPO_ROOT / "results" / "fixtures" / "rp6-policy-hardened" / "report_card.json")
    policy_probe = report_card["policy_probes"][0]
    aggregate = {
        "case_count": len(rows),
        "policy_probe_count": 1,
        "runtime_profiles": ["RP2", "RP3", "RP6"],
        "runtime_aggregates": runtime_aggregates,
        "rp2_to_rp6_realized_reduction": runtime_aggregates["RP2"]["realized_contract_violations"]
        - runtime_aggregates["RP6"]["realized_contract_violations"],
        "rp2_to_rp6_canary_reduction": runtime_aggregates["RP2"]["canary_observations"]
        - runtime_aggregates["RP6"]["canary_observations"],
        "rp6_missing_output_increase_vs_rp2": runtime_aggregates["RP6"]["missing_expected_outputs"]
        - runtime_aggregates["RP2"]["missing_expected_outputs"],
        "rp6_policy_probe_attempted_overreach": policy_probe["summary"]["attempted_overreach"],
        "rp6_pair_count": rp6_pair_total,
        "rp6_mitigation_pair_count": rp6_mitigation_pair_total,
    }
    return aggregate, rows, policy_probe


def summary_without_event_count(summary: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in summary.items() if key != "event_count"}


def validate_repeat_observation(
    observation: dict[str, Any],
    key: tuple[str, str],
    expected_repeat_id: str,
) -> dict[str, Any]:
    require(observation.get("repeat_id") == expected_repeat_id, f"{key}: repeat ID mismatch")
    findings_path = resolve_repo_path(observation["findings_path"])
    trace_path = resolve_repo_path(observation["trace_path"])
    require(findings_path.is_file(), f"missing repeat findings: {findings_path}")
    require(trace_path.is_file(), f"missing repeat trace: {trace_path}")
    findings = load_json(findings_path)
    summary = findings["summary"]
    require(summary == observation["summary"], f"{findings_path}: stale repeat summary")
    require(
        summary_without_event_count(summary) == observation["summary_without_event_count"],
        f"{findings_path}: stale event-count-excluded summary",
    )
    require(str(findings.get("repeat_id")) == expected_repeat_id, f"{findings_path}: findings repeat ID mismatch")
    events = validate_trace_file(trace_path)
    require(len(events) == summary["event_count"], f"{trace_path}: event count mismatch")
    require({event["runtime_profile"] for event in events} == {"RP6"}, f"{trace_path}: non-RP6 event")
    require(
        {str(event["repeat_id"]) for event in events} == {expected_repeat_id},
        f"{trace_path}: repeat ID mismatch",
    )
    return summary


def recompute_repeat_stability(cases: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rp6_cases = rp6_case_map()
    rows = []
    for row in cases:
        key = case_key(row)
        observations = row.get("observations")
        require(isinstance(observations, list) and len(observations) == 3, f"{key}: repeat observation count mismatch")
        require(row.get("repeat_ids") == ["1", "2", "3"], f"{key}: repeat IDs mismatch")
        first_observation = observations[0]
        report_card_case = rp6_cases[key]
        require(first_observation.get("source") == "rp6_report_card", f"{key}: first observation source mismatch")
        require(
            first_observation.get("findings_path") == report_card_case["findings_path"],
            f"{key}: first findings path mismatch",
        )
        require(
            first_observation.get("trace_path") == report_card_case["trace_path"],
            f"{key}: first trace path mismatch",
        )
        require(first_observation.get("summary") == report_card_case["summary"], f"{key}: first summary mismatch")
        for observation, repeat_id in zip(observations[1:], ["2", "3"], strict=True):
            require(observation.get("source") == "strengthening_repeat", f"{key}: repeat {repeat_id} source mismatch")
        summaries = [
            validate_repeat_observation(observation, key, repeat_id)
            for observation, repeat_id in zip(observations, ["1", "2", "3"], strict=True)
        ]
        first_summary = summaries[0]
        first_comparable_summary = summary_without_event_count(first_summary)
        stable_excluding_event_count = all(
            summary_without_event_count(summary) == first_comparable_summary
            for summary in summaries
        )
        stable_including_event_count = all(summary == first_summary for summary in summaries)
        rows.append(
            {
                "case_id": row["case_id"],
                "family": row["family"],
                "observation_count": len(observations),
                "observations": row["observations"],
                "repeat_ids": ["1", "2", "3"],
                "stable_summary_excluding_event_count": stable_excluding_event_count,
                "stable_summary_including_event_count": stable_including_event_count,
                "variant_id": row["variant_id"],
            }
        )
    stable_cases = [
        row
        for row in rows
        if row["observation_count"] >= 3 and row["stable_summary_excluding_event_count"]
    ]
    observations = [
        observation
        for row in rows
        for observation in row["observations"]
    ]
    aggregate = {
        "case_count": len(rows),
        "deterministic_stability_claims_supported": len(stable_cases),
        "minimum_repeats_for_deterministic_stability_claim": 3,
        "repeat_ids": ["1", "2", "3"],
        "repeat_observation_count": len(observations),
        "repeats_per_case": 3,
        "rp6_canary_observations": sum(
            observation["summary"]["canary_observation_count"]
            for observation in observations
        ),
        "rp6_realized_contract_violations": sum(
            observation["summary"]["realized_contract_violations"]
            for observation in observations
        ),
        "statistical_repeat_stability_claims_supported": 0,
        "summary_match_count_excluding_event_count": sum(
            1 for row in rows if row["stable_summary_excluding_event_count"]
        ),
        "summary_match_count_including_event_count": sum(
            1 for row in rows if row["stable_summary_including_event_count"]
        ),
        "trace_valid_count": sum(
            1 for observation in observations if observation["summary"]["trace_valid"] is True
        ),
    }
    return aggregate, rows


def validate_claim_boundary_false(report: dict[str, Any], keys: tuple[str, ...], label: str) -> None:
    claim_boundary = report.get("claim_boundary", {})
    require(isinstance(claim_boundary, dict), f"{label}: claim boundary missing")
    for key in keys:
        require(claim_boundary.get(key) is False, f"{label}: claim boundary {key} must be false")


def validate_static_scanner_baseline() -> None:
    report = load_json(OUT_ROOT / "static_scanner_baseline.json")
    require(report.get("schema_version") == "0.1", "static scanner schema mismatch")
    require(report.get("report_type") == "static_scanner_baseline", "static scanner report type mismatch")
    boundary = report.get("boundary", "")
    require("not runtime evidence" in boundary, "static scanner boundary missing runtime exclusion")
    validate_claim_boundary_false(
        report,
        (
            "commercial_runtime_claim",
            "defense_success_claim",
            "prevalence_claim",
            "public_network_claim",
            "runtime_behavior_claim",
            "semia_equivalence_claim",
        ),
        "static scanner",
    )
    recomputed = strengthening_baselines.build_static_scanner_report(REPO_ROOT, rp6_runner.CASES)
    require(report.get("aggregate") == recomputed["aggregate"], "static scanner aggregate is stale")
    compare_rows(
        report.get("cases", []),
        recomputed["cases"],
        [
            "contract",
            "finding_count",
            "finding_families",
            "findings",
            "scanned_file_count",
            "scanned_files",
            "source_scope",
            "variant_id",
            "workspace",
        ],
        "static scanner",
    )
    markdown_path = OUT_ROOT / "static_scanner_baseline.md"
    require(markdown_path.is_file(), "missing static scanner Markdown")
    markdown = markdown_path.read_text(encoding="utf-8")
    require(report["boundary"] in markdown, "static scanner Markdown boundary is stale")
    require(f"Static findings: `{report['aggregate']['static_finding_count']}`" in markdown, "static scanner Markdown aggregate is stale")


def validate_reachability_approximation() -> None:
    static_report = load_json(OUT_ROOT / "static_scanner_baseline.json")
    report = load_json(OUT_ROOT / "reachability_approximation.json")
    require(report.get("schema_version") == "0.1", "reachability approximation schema mismatch")
    require(report.get("report_type") == "semia_style_reachability_approximation", "reachability approximation report type mismatch")
    boundary = report.get("boundary", "")
    require("not a Semia reproduction" in boundary, "reachability boundary missing Semia reproduction exclusion")
    require("Semia equivalence" in boundary, "reachability boundary missing Semia equivalence exclusion")
    validate_claim_boundary_false(
        report,
        (
            "commercial_runtime_claim",
            "defense_success_claim",
            "prevalence_claim",
            "public_network_claim",
            "runtime_confirmation_claim",
            "semia_equivalence_claim",
            "semia_reproduction_claim",
        ),
        "reachability approximation",
    )
    recomputed = strengthening_baselines.build_reachability_approximation_report(
        REPO_ROOT,
        rp6_runner.CASES,
        static_report,
    )
    require(report.get("aggregate") == recomputed["aggregate"], "reachability approximation aggregate is stale")
    compare_rows(
        report.get("cases", []),
        recomputed["cases"],
        [
            "contract",
            "contract_deny_surface_counts",
            "candidate_count",
            "candidates",
            "static_finding_count",
            "variant_id",
        ],
        "reachability approximation",
    )
    aggregate = report["aggregate"]
    require(aggregate.get("runtime_confirmation_claims_supported") == 0, "reachability runtime confirmation claim leaked")
    require(aggregate.get("semia_equivalence_claims_supported") == 0, "reachability Semia equivalence claim leaked")
    require(aggregate.get("semia_reproduction_claims_supported") == 0, "reachability Semia reproduction claim leaked")
    markdown_path = OUT_ROOT / "reachability_approximation.md"
    require(markdown_path.is_file(), "missing reachability approximation Markdown")
    markdown = markdown_path.read_text(encoding="utf-8")
    require(report["boundary"] in markdown, "reachability Markdown boundary is stale")
    require(f"Approximation candidates: `{aggregate['candidate_count']}`" in markdown, "reachability Markdown aggregate is stale")


def validate_action_boundary_baseline() -> None:
    report = load_json(OUT_ROOT / "action_boundary_baseline.json")
    require(report.get("schema_version") == "0.1", "action-boundary schema mismatch")
    require(report.get("report_type") == "action_boundary_baseline", "action-boundary report type mismatch")
    boundary = report.get("boundary", "")
    require("not a reproduction" in boundary, "action-boundary boundary missing reproduction exclusion")
    require("defense success" in boundary, "action-boundary boundary missing defense-success exclusion")
    validate_claim_boundary_false(
        report,
        (
            "clawguard_equivalence_claim",
            "clawguard_reproduction_claim",
            "commercial_runtime_claim",
            "defense_success_claim",
            "public_network_claim",
            "task_shield_equivalence_claim",
            "task_shield_reproduction_claim",
        ),
        "action-boundary baseline",
    )
    recomputed = strengthening_baselines.build_action_boundary_baseline_report(REPO_ROOT, rp6_runner.CASES)
    require(report.get("aggregate") == recomputed["aggregate"], "action-boundary aggregate is stale")
    compare_rows(
        report.get("cases", []),
        recomputed["cases"],
        [
            "command",
            "command_contract_allowed",
            "contract",
            "controlled_fixture_command",
            "deny_surface_counts_considered",
            "requires_runtime_monitoring",
            "review_flag",
            "review_reason",
            "style_boundary",
            "task_relevance_basis",
            "variant_id",
        ],
        "action-boundary",
    )
    aggregate = report["aggregate"]
    require(aggregate.get("clawguard_reproduction_claims_supported") == 0, "ClawGuard reproduction claim leaked")
    require(aggregate.get("task_shield_reproduction_claims_supported") == 0, "Task Shield reproduction claim leaked")
    markdown_path = OUT_ROOT / "action_boundary_baseline.md"
    require(markdown_path.is_file(), "missing action-boundary Markdown")
    markdown = markdown_path.read_text(encoding="utf-8")
    require(report["boundary"] in markdown, "action-boundary Markdown boundary is stale")
    require(f"Commands checked: `{aggregate['command_actions_checked']}`" in markdown, "action-boundary Markdown aggregate is stale")


def validate_least_privilege() -> None:
    report = load_json(OUT_ROOT / "least_privilege_baseline.json")
    require(report.get("schema_version") == "0.1", "least-privilege schema mismatch")
    recomputed_aggregate, recomputed_cases = recompute_least_privilege()
    require(report.get("aggregate") == recomputed_aggregate, "least-privilege aggregate is stale")
    require(report.get("aggregate") == EXPECTED_LEAST_PRIVILEGE, "least-privilege aggregate mismatch")
    cases = report.get("cases")
    require(isinstance(cases, list) and len(cases) == EXPECTED_LEAST_PRIVILEGE["case_count"], "least-privilege case count mismatch")
    compare_rows(
        cases,
        recomputed_cases,
        [
            "contract",
            "expectation",
            "expectation_passed",
            "is_benign",
            "policy_shape",
            "rp6_findings_path",
            "rp6_summary",
            "variant_id",
        ],
        "least-privilege",
    )
    for row in cases:
        require(row.get("expectation_passed") is True, f"{row.get('family')}/{row.get('case_id')}: expectation failed")
        shape = row.get("policy_shape", {})
        require(shape.get("total_allow_rules", 0) > 0, f"{row.get('family')}/{row.get('case_id')}: no allow rules")
        require(shape.get("total_deny_rules", 0) > 0, f"{row.get('family')}/{row.get('case_id')}: no deny rules")
        require(resolve_repo_path(row["rp6_findings_path"]).is_file(), "missing RP6 findings path")


def validate_ladder() -> None:
    report = load_json(OUT_ROOT / "rp6_mitigation_ladder.json")
    require(report.get("schema_version") == "0.1", "mitigation ladder schema mismatch")
    recomputed_aggregate, recomputed_cases = recompute_mitigation_ladder()
    require(report.get("aggregate") == recomputed_aggregate, "mitigation ladder aggregate is stale")
    require(report.get("aggregate") == EXPECTED_LADDER, "mitigation ladder aggregate mismatch")
    cases = report.get("cases")
    require(isinstance(cases, list) and len(cases) == EXPECTED_LADDER["case_count"], "mitigation ladder case count mismatch")
    compare_rows(cases, recomputed_cases, ["is_benign", "runtime_summaries", "variant_id"], "mitigation ladder")
    for row in cases:
        summaries = row.get("runtime_summaries", {})
        require(sorted(summaries) == ["RP2", "RP3", "RP6"], f"{row.get('family')}/{row.get('case_id')}: runtime summaries mismatch")
        for runtime, summary in summaries.items():
            require(summary.get("trace_valid") is True, f"{row.get('family')}/{row.get('case_id')}/{runtime}: trace invalid")


def validate_minimal_contrast() -> None:
    report = load_json(REPO_ROOT / "results" / "fixtures" / "rp6-policy-hardened" / "ablations" / "minimal_report_card.json")
    require(report.get("schema_version") == "0.1", "minimal contrast schema mismatch")
    recomputed_aggregate, recomputed_cases, recomputed_probe = recompute_minimal_contrast()
    require(report.get("aggregate") == recomputed_aggregate, "minimal contrast aggregate is stale")
    require(report.get("aggregate") == EXPECTED_MINIMAL_CONTRAST, "minimal contrast aggregate mismatch")
    cases = report.get("cases")
    require(isinstance(cases, list) and len(cases) == EXPECTED_MINIMAL_CONTRAST["case_count"], "minimal contrast case count mismatch")
    compare_rows(
        cases,
        recomputed_cases,
        [
            "comparison_path",
            "rp6_mitigation_pair_count",
            "rp6_pair_count",
            "rp6_pairs_are_mitigation_only",
            "runtime_summaries",
            "variant_id",
        ],
        "minimal contrast",
    )
    for row in cases:
        require(row.get("rp6_pair_count", 0) > 0, f"{row.get('family')}/{row.get('case_id')}: no RP6 pair coverage")
        require(row.get("rp6_pairs_are_mitigation_only") is True, f"{row.get('family')}/{row.get('case_id')}: RP6 pair classification mismatch")
        require(resolve_repo_path(row["comparison_path"]).is_file(), f"missing minimal contrast comparison {row.get('comparison_path')}")
    policy_probe = report.get("policy_probe", {})
    require(policy_probe == recomputed_probe, "minimal contrast policy probe is stale")
    require(policy_probe.get("summary", {}).get("attempted_overreach") == 2, "minimal contrast policy probe mismatch")
    require((REPO_ROOT / "results" / "fixtures" / "rp6-policy-hardened" / "ablations" / "minimal_matrix.csv").is_file(), "missing minimal matrix CSV")


def component_summary_delta(baseline: dict[str, Any], ablated: dict[str, Any]) -> dict[str, int]:
    return {
        field: int(ablated.get(field, 0)) - int(baseline.get(field, 0))
        for field in COMPONENT_SUMMARY_FIELDS
    }


def component_utility_preserved(summary: dict[str, Any]) -> bool:
    return (
        summary.get("trace_valid") is True
        and summary.get("missing_expected_outputs") == 0
        and summary.get("output_oracle_failures") == 0
    )


def component_security_regression_observed(delta: dict[str, int]) -> bool:
    return (
        delta["realized_contract_violations"] > 0
        or delta["canary_observation_count"] > 0
        or (delta["attempted_overreach"] < 0 and delta["realized_contract_violations"] > 0)
    )


def component_baseline_row(row: dict[str, Any], rp6_cases: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    if row["case_id"] == "network_policy_probe":
        return load_json(REPO_ROOT / "results" / "fixtures" / "rp6-policy-hardened" / "report_card.json")["policy_probes"][0]
    return rp6_cases[case_key(row)]


def contract_persistence_path_globs(contract_path: Path) -> list[str]:
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    access = contract.get("access", {}) if isinstance(contract, dict) else {}
    persistence = access.get("persistence", {}) if isinstance(access, dict) else {}
    if not isinstance(persistence, dict):
        return []
    path_globs = []
    for side in ("allow", "deny"):
        for rule in persistence.get(side, []) or []:
            match = rule.get("match", {}) if isinstance(rule, dict) else {}
            path_glob = match.get("path_glob") if isinstance(match, dict) else None
            if isinstance(path_glob, str):
                normalized = normalize_path(path_glob)
                if normalized not in path_globs:
                    path_globs.append(normalized)
    return path_globs


def validate_persistence_cache_ablation_row(
    row: dict[str, Any],
    events: list[dict[str, Any]],
    execution_plan: dict[str, Any],
) -> None:
    if row["component_id"] != "persistence_cache_access":
        return

    key = case_key(row)
    require(row.get("disabled_components") == ["persistence_cache_access"], f"{key}: persistence component mismatch")
    contract_globs = contract_persistence_path_globs(resolve_repo_path(row["contract"]))
    require(contract_globs, f"{key}: persistence ablation contract has no persistence path globs")
    policy = execution_plan.get("policy", {})
    write_allow = policy.get("write_allow", []) if isinstance(policy, dict) else []
    write_deny = policy.get("write_deny", []) if isinstance(policy, dict) else []
    ablation_write_globs = [
        normalize_path(rule["path_glob"])
        for rule in write_allow
        if isinstance(rule, dict) and str(rule.get("id", "")).startswith("RP6-ABL-PER-W-")
    ]
    require(ablation_write_globs == contract_globs, f"{key}: persistence ablation write surface mismatch")
    require(write_deny, f"{key}: persistence ablation removed normal filesystem write deny rules")
    require(
        not any(rule.get("id") == "RP6-ABL-FS-W-ALLOW-ALL" for rule in write_allow if isinstance(rule, dict)),
        f"{key}: persistence ablation used broad filesystem write allowance",
    )

    persistence_events = [event for event in events if event["event_type"] == "persistence.write"]
    if row["case_role"] != "benign_control":
        require(persistence_events, f"{key}: adversarial persistence ablation row has no persistence.write event")
    for event in persistence_events:
        metadata = event.get("metadata", {}) if isinstance(event.get("metadata"), dict) else {}
        target = event.get("normalized_target") or event.get("target") or ""
        require(metadata.get("store_type") == "file", f"{key}: persistence event is not file-backed")
        require(metadata.get("retention_scope") == "workspace", f"{key}: persistence event scope is not workspace")
        require(metadata.get("post_cleanup_allowed") is False, f"{key}: persistence event cleanup boundary mismatch")
        require(
            any(path_matches_glob(path_glob, target) for path_glob in contract_globs),
            f"{key}: persistence event target is outside contract persistence/cache path globs",
        )

    cache_writes = [
        event
        for event in events
        if event["event_type"] == "filesystem.write"
        and str(event.get("matched_allow_rule", "")).startswith("RP6-ABL-PER-W-")
    ]
    if row["case_role"] != "benign_control":
        require(cache_writes, f"{key}: adversarial persistence ablation row has no cache-path filesystem write")
    for event in cache_writes:
        target = event.get("normalized_target") or event.get("target") or ""
        require(event["event_status"] == "succeeded", f"{key}: cache-path filesystem write did not succeed")
        require(
            any(path_matches_glob(path_glob, target) for path_glob in contract_globs),
            f"{key}: cache-path filesystem write is outside contract persistence/cache path globs",
        )


def recompute_component_aggregate(rows: list[dict[str, Any]], components: list[dict[str, Any]]) -> dict[str, Any]:
    def sum_summary(source: str, field: str) -> int:
        return sum(int(row[source][field]) for row in rows)

    component_dual_coverage = 0
    for component in components:
        component_rows = [row for row in rows if row["component_id"] == component["component_id"]]
        roles = {row["case_role"] for row in component_rows}
        if "benign_control" in roles and any(role != "benign_control" for role in roles):
            component_dual_coverage += 1
    return {
        "case_count": len(rows),
        "component_count": len(components),
        "components_with_benign_and_adversarial_coverage": component_dual_coverage,
        "runtime_profile": "RP6",
        "benign_control_cases": sum(1 for row in rows if row["case_role"] == "benign_control"),
        "adversarial_or_probe_cases": sum(1 for row in rows if row["case_role"] != "benign_control"),
        "expectation_passed_cases": sum(1 for row in rows if row["expectation_passed"]),
        "security_regression_cases": sum(1 for row in rows if row["security_regression_observed"]),
        "utility_preserved_cases": sum(1 for row in rows if row["utility_preserved"]),
        "rp6_baseline_realized_contract_violations": sum_summary("baseline_summary", "realized_contract_violations"),
        "rp6_ablated_realized_contract_violations": sum_summary("ablated_summary", "realized_contract_violations"),
        "realized_contract_violation_delta": sum(row["delta"]["realized_contract_violations"] for row in rows),
        "rp6_baseline_canary_observations": sum_summary("baseline_summary", "canary_observation_count"),
        "rp6_ablated_canary_observations": sum_summary("ablated_summary", "canary_observation_count"),
        "canary_observation_delta": sum(row["delta"]["canary_observation_count"] for row in rows),
        "rp6_baseline_missing_expected_outputs": sum_summary("baseline_summary", "missing_expected_outputs"),
        "rp6_ablated_missing_expected_outputs": sum_summary("ablated_summary", "missing_expected_outputs"),
        "missing_expected_output_delta": sum(row["delta"]["missing_expected_outputs"] for row in rows),
    }


def recompute_component_rows(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rp6_cases = rp6_case_map()
    rows = []
    for row in cases:
        key = (row["family"], row["case_id"])
        disabled_components = row.get("disabled_components")
        require(isinstance(disabled_components, list) and disabled_components, f"{key}: disabled components missing")
        baseline = component_baseline_row(row, rp6_cases)
        require(row.get("baseline_summary") == baseline["summary"], f"{key}: stale component baseline summary")
        require(row.get("baseline_trace_path") == baseline["trace_path"], f"{key}: stale component baseline trace")
        require(row.get("baseline_findings_path") == baseline["findings_path"], f"{key}: stale component baseline findings")

        findings_path = resolve_repo_path(row["ablated_findings_path"])
        trace_path = resolve_repo_path(row["ablated_trace_path"])
        require(findings_path.is_file(), f"{key}: missing component findings {findings_path}")
        require(trace_path.is_file(), f"{key}: missing component trace {trace_path}")
        findings = load_json(findings_path)
        require(findings.get("component_id") == row["component_id"], f"{findings_path}: component id mismatch")
        require(findings.get("disabled_components") == disabled_components, f"{findings_path}: disabled component mismatch")
        require(findings.get("summary") == row["ablated_summary"], f"{findings_path}: stale ablated summary")
        require(findings.get("baseline_summary") == row["baseline_summary"], f"{findings_path}: stale baseline summary")
        events = validate_trace_file(trace_path)
        require(len(events) == row["ablated_summary"]["event_count"], f"{trace_path}: event count mismatch")
        require({event["runtime_profile"] for event in events} == {"RP6"}, f"{trace_path}: non-RP6 event")
        execution_plan = load_json(trace_path.parent / "execution_plan.json")
        require(
            execution_plan.get("ablation_disabled_components") == disabled_components,
            f"{trace_path}: execution plan ablation component mismatch",
        )
        validate_persistence_cache_ablation_row(row, events, execution_plan)
        delta = component_summary_delta(row["baseline_summary"], row["ablated_summary"])
        require(row.get("delta") == delta, f"{key}: component delta mismatch")
        utility = component_utility_preserved(row["ablated_summary"])
        security = component_security_regression_observed(delta)
        require(row.get("utility_preserved") is utility, f"{key}: utility flag mismatch")
        require(row.get("security_regression_observed") is security, f"{key}: security-regression flag mismatch")
        expected_pass = utility if row["case_role"] == "benign_control" else security
        require(row.get("expectation_passed") is expected_pass, f"{key}: expectation flag mismatch")
        require(row.get("runtime_profile") == "RP6", f"{key}: runtime profile mismatch")
        rows.append(row)
    return rows


def recompute_component_summaries(rows: list[dict[str, Any]], components: list[dict[str, Any]]) -> list[dict[str, Any]]:
    recomputed = []
    for component in components:
        component_id = component["component_id"]
        profile_path = resolve_repo_path(component["profile_path"])
        require(profile_path.is_file(), f"{component_id}: missing generated profile")
        profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
        metadata = profile.get("metadata", {}) if isinstance(profile, dict) else {}
        ablation = metadata.get("rp6_component_ablation", {}) if isinstance(metadata, dict) else {}
        require(ablation.get("component_id") == component_id, f"{component_id}: generated profile component mismatch")
        require(
            ablation.get("disabled_components") == component["disabled_components"],
            f"{component_id}: generated profile disabled component mismatch",
        )
        component_rows = [row for row in rows if row["component_id"] == component_id]
        recomputed.append(
            {
                "component_id": component_id,
                "component_name": component["component_name"],
                "disabled_components": component["disabled_components"],
                "profile_path": component["profile_path"],
                "case_count": len(component_rows),
                "expectation_passed_cases": sum(1 for row in component_rows if row["expectation_passed"]),
                "security_regression_cases": sum(1 for row in component_rows if row["security_regression_observed"]),
                "utility_preserved_cases": sum(1 for row in component_rows if row["utility_preserved"]),
                "realized_contract_violation_delta": sum(
                    row["delta"]["realized_contract_violations"] for row in component_rows
                ),
                "canary_observation_delta": sum(row["delta"]["canary_observation_count"] for row in component_rows),
            }
        )
    return recomputed


def validate_component_companion_artifacts(report: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    ablation_root = REPO_ROOT / "results" / "fixtures" / "rp6-policy-hardened" / "ablations"
    matrix_path = ablation_root / "component_matrix.csv"
    markdown_path = ablation_root / "component_report_card.md"
    require(matrix_path.is_file(), "missing component matrix CSV")
    require(markdown_path.is_file(), "missing component report Markdown")

    expected_columns = [
        "component_id",
        "family",
        "case_id",
        "case_role",
        "expectation_passed",
        "utility_preserved",
        "security_regression_observed",
        "baseline_realized",
        "ablated_realized",
        "baseline_canary",
        "ablated_canary",
        "baseline_missing_outputs",
        "ablated_missing_outputs",
    ]
    with matrix_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames == expected_columns, "component matrix CSV header mismatch")
        observed_rows = list(reader)

    expected_rows = [
        {
            "component_id": row["component_id"],
            "family": row["family"],
            "case_id": row["case_id"],
            "case_role": row["case_role"],
            "expectation_passed": str(row["expectation_passed"]).lower(),
            "utility_preserved": str(row["utility_preserved"]).lower(),
            "security_regression_observed": str(row["security_regression_observed"]).lower(),
            "baseline_realized": str(row["baseline_summary"]["realized_contract_violations"]),
            "ablated_realized": str(row["ablated_summary"]["realized_contract_violations"]),
            "baseline_canary": str(row["baseline_summary"]["canary_observation_count"]),
            "ablated_canary": str(row["ablated_summary"]["canary_observation_count"]),
            "baseline_missing_outputs": str(row["baseline_summary"]["missing_expected_outputs"]),
            "ablated_missing_outputs": str(row["ablated_summary"]["missing_expected_outputs"]),
        }
        for row in rows
    ]
    require(observed_rows == expected_rows, "component matrix CSV is stale")

    markdown = markdown_path.read_text(encoding="utf-8")
    require("# RP6 Component Ablation Report Card" in markdown, "component Markdown title mismatch")
    require(report["boundary"] in markdown, "component Markdown boundary is stale")
    for component in report["components"]:
        require(component["component_id"] in markdown, f"component Markdown missing {component['component_id']}")
    aggregate = report["aggregate"]
    for text in (
        f"Components: `{aggregate['component_count']}`",
        f"Cases: `{aggregate['case_count']}`",
        f"Expectation-passed rows: `{aggregate['expectation_passed_cases']}`",
        f"Realized contract-violation delta: `{aggregate['realized_contract_violation_delta']}`",
        f"Canary-observation delta: `{aggregate['canary_observation_delta']}`",
    ):
        require(text in markdown, f"component Markdown missing aggregate text {text!r}")


def validate_component_ablation() -> None:
    report = load_json(REPO_ROOT / "results" / "fixtures" / "rp6-policy-hardened" / "ablations" / "component_report_card.json")
    require(report.get("schema_version") == "0.1", "component ablation schema mismatch")
    require(report.get("report_type") == "rp6_component_ablation", "component ablation report type mismatch")
    boundary = report.get("boundary", "")
    require("not a commercial runtime" in boundary, "component ablation boundary missing commercial-runtime exclusion")
    claim_boundary = report.get("claim_boundary", {})
    for key in ("commercial_runtime_claim", "defense_success_claim", "public_network_claim", "semia_equivalence_claim", "statistical_claim"):
        require(claim_boundary.get(key) is False, f"component ablation claim boundary {key} must be false")
    cases = report.get("cases")
    components = report.get("components")
    require(isinstance(cases, list) and len(cases) == EXPECTED_COMPONENT_ABLATION["case_count"], "component ablation case count mismatch")
    require(isinstance(components, list) and len(components) == EXPECTED_COMPONENT_ABLATION["component_count"], "component ablation component count mismatch")
    require(sorted(component["component_id"] for component in components) == EXPECTED_COMPONENT_IDS, "component ID set mismatch")
    rows = recompute_component_rows(cases)
    recomputed_components = recompute_component_summaries(rows, components)
    require(components == recomputed_components, "component summaries are stale")
    recomputed_aggregate = recompute_component_aggregate(rows, components)
    require(report.get("aggregate") == recomputed_aggregate, "component ablation aggregate is stale")
    require(report.get("aggregate") == EXPECTED_COMPONENT_ABLATION, "component ablation aggregate mismatch")
    validate_component_companion_artifacts(report, rows)
    for component in components:
        component_rows = [row for row in rows if row["component_id"] == component["component_id"]]
        roles = {row["case_role"] for row in component_rows}
        require("benign_control" in roles, f"{component['component_id']}: missing benign control")
        require(any(role != "benign_control" for role in roles), f"{component['component_id']}: missing adversarial/probe control")
        require(component["expectation_passed_cases"] == component["case_count"], f"{component['component_id']}: expectation failed")


def validate_repeat_stability() -> None:
    report = load_json(OUT_ROOT / "repeat-stability" / "repeat_stability.json")
    require(report.get("schema_version") == "0.1", "repeat-stability schema mismatch")
    cases = report.get("cases")
    require(isinstance(cases, list) and len(cases) == EXPECTED_REPEAT["case_count"], "repeat-stability case count mismatch")
    recomputed_aggregate, recomputed_cases = recompute_repeat_stability(cases)
    require(report.get("aggregate") == recomputed_aggregate, "repeat-stability aggregate is stale")
    require(report.get("aggregate") == EXPECTED_REPEAT, "repeat-stability aggregate mismatch")
    compare_rows(
        cases,
        recomputed_cases,
        [
            "observation_count",
            "observations",
            "repeat_ids",
            "stable_summary_excluding_event_count",
            "stable_summary_including_event_count",
            "variant_id",
        ],
        "repeat stability",
    )
    for row in cases:
        require(row.get("observation_count") == 3, f"{row.get('family')}/{row.get('case_id')}: repeat count mismatch")
        require(row.get("stable_summary_excluding_event_count") is True, f"{row.get('family')}/{row.get('case_id')}: repeat summary mismatch")
        require(row.get("stable_summary_including_event_count") is True, f"{row.get('family')}/{row.get('case_id')}: repeat event-count mismatch")


def validate_index() -> None:
    index = load_json(OUT_ROOT / "index.json")
    require(index.get("schema_version") == "0.1", "strengthening index schema mismatch")
    reports = index.get("reports")
    require(isinstance(reports, dict), "strengthening index reports missing")
    require(reports == EXPECTED_INDEX_REPORTS, "strengthening index report set mismatch")
    aggregates = index.get("aggregates")
    require(isinstance(aggregates, dict), "strengthening index aggregates missing")
    require(set(aggregates) == set(EXPECTED_INDEX_REPORTS), "strengthening index aggregate set mismatch")
    for key, path in reports.items():
        report_path = resolve_repo_path(path)
        require(report_path.is_file(), f"missing indexed report {path}")
        report = load_json(report_path)
        require(aggregates.get(key) == report.get("aggregate"), f"strengthening index aggregate stale for {key}")


def main() -> int:
    validate_static_scanner_baseline()
    validate_reachability_approximation()
    validate_action_boundary_baseline()
    validate_least_privilege()
    validate_ladder()
    validate_minimal_contrast()
    validate_component_ablation()
    validate_repeat_stability()
    validate_index()
    print("validated strengthening evidence artifacts")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"strengthening evidence validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
