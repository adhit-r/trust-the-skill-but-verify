#!/usr/bin/env python3
"""Generate strengthening evidence for the current SkillDiff paper package."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_ROOT))

import run_rp6_policy_hardened_mvp as rp6_runner  # noqa: E402
import strengthening_baselines  # noqa: E402


PYTHON = sys.executable
OUT_ROOT = REPO_ROOT / "results" / "fixtures" / "strengthening"
REPEAT_ROOT = OUT_ROOT / "repeat-stability"
REPEAT_RUN_ROOT = REPEAT_ROOT / "_runs"
RP6_REPORT_CARD = REPO_ROOT / "results" / "fixtures" / "rp6-policy-hardened" / "report_card.json"
RP6_ABLATION_ROOT = REPO_ROOT / "results" / "fixtures" / "rp6-policy-hardened" / "ablations"
COMPONENT_ABLATION_RUN_ROOT = RP6_ABLATION_ROOT / "_component_runs"
COMPONENT_ABLATION_INPUT_ROOT = RP6_ABLATION_ROOT / "_component_inputs"
GENERATED_REPEAT_IDS = ("2", "3")
STABILITY_REPEAT_IDS = ("1", *GENERATED_REPEAT_IDS)
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
COMPONENT_ABLATIONS = [
    {
        "component_id": "filesystem_read_scope",
        "component_name": "contract-scoped file-read policy",
        "disabled_components": ["filesystem_read_scope"],
        "cases": [
            {"family": "repo-audit", "case_id": "benign", "case_role": "benign_control"},
            {"family": "repo-audit", "case_id": "adversarial", "case_role": "adversarial_control"},
        ],
    },
    {
        "component_id": "filesystem_write_scope",
        "component_name": "contract-scoped file-write policy",
        "disabled_components": ["filesystem_write_scope"],
        "cases": [
            {"family": "docs-forge", "case_id": "p2_benign", "case_role": "benign_control"},
            {"family": "docs-forge", "case_id": "p2_adversarial", "case_role": "adversarial_control"},
        ],
    },
    {
        "component_id": "network_egress_blocker",
        "component_name": "network egress blocker",
        "disabled_components": ["network_egress_blocker"],
        "cases": [
            {"family": "network-egress", "case_id": "benign", "case_role": "benign_control"},
            {"family": "network-egress", "case_id": "network_policy_probe", "case_role": "adversarial_probe"},
        ],
    },
    {
        "component_id": "semantic_tool_policy",
        "component_name": "semantic tool-call policy rewriter",
        "disabled_components": ["semantic_tool_policy"],
        "cases": [
            {"family": "mcp-tool-workflow", "case_id": "benign", "case_role": "benign_control"},
            {"family": "mcp-tool-workflow", "case_id": "adversarial", "case_role": "adversarial_control"},
        ],
    },
    {
        "component_id": "approval_requirement",
        "component_name": "deterministic approval transcript requirement",
        "disabled_components": ["approval_requirement"],
        "cases": [
            {"family": "repo-audit", "case_id": "benign", "case_role": "benign_control"},
            {"family": "docs-forge", "case_id": "p2_adversarial", "case_role": "adversarial_control"},
        ],
    },
    {
        "component_id": "persistence_cache_access",
        "component_name": "file-backed persistence/cache policy",
        "disabled_components": ["persistence_cache_access"],
        "cases": [
            {"family": "mcp-tool-workflow", "case_id": "benign", "case_role": "benign_control"},
            {"family": "mcp-tool-workflow", "case_id": "adversarial", "case_role": "adversarial_control"},
        ],
    },
]
COMPONENT_SUMMARY_FIELDS = (
    "attempted_overreach",
    "canary_observation_count",
    "event_count",
    "missing_expected_outputs",
    "output_oracle_failures",
    "realized_contract_violations",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def is_benign(case: dict[str, Any]) -> bool:
    case_id = str(case["case_id"])
    return case_id == "benign" or case_id.endswith("_benign")


def mvp_findings_path(case: dict[str, Any], runtime_profile: str) -> Path:
    family = case["family"]
    case_id = case["case_id"]
    suffix = "_rp3_contract_findings.json" if runtime_profile == "RP3" else "_contract_findings.json"
    return REPO_ROOT / "results" / "mvp" / family / f"{case_id}{suffix}"


def rp6_case_map() -> dict[tuple[str, str], dict[str, Any]]:
    report = load_json(RP6_REPORT_CARD)
    return {(case["family"], case["case_id"]): case for case in report["cases"]}


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


def generate_least_privilege_baseline() -> dict[str, Any]:
    rp6_cases = rp6_case_map()
    rows = []
    for case in rp6_runner.CASES:
        key = (case["family"], case["case_id"])
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
    report = {
        "schema_version": "0.1",
        "report_type": "least_privilege_policy_baseline",
        "boundary": (
            "Static contract-derived least-privilege baseline evaluated against existing RP6 report-card outcomes. "
            "This is not a separate runtime execution or defense-success claim."
        ),
        "aggregate": aggregate,
        "cases": rows,
    }
    write_json(OUT_ROOT / "least_privilege_baseline.json", report)
    write_least_privilege_markdown(report)
    return report


def generate_static_scanner_baseline() -> dict[str, Any]:
    report = strengthening_baselines.build_static_scanner_report(REPO_ROOT, rp6_runner.CASES)
    write_json(OUT_ROOT / "static_scanner_baseline.json", report)
    strengthening_baselines.write_static_scanner_markdown(OUT_ROOT / "static_scanner_baseline.md", report)
    return report


def generate_reachability_approximation(static_scanner: dict[str, Any]) -> dict[str, Any]:
    report = strengthening_baselines.build_reachability_approximation_report(
        REPO_ROOT,
        rp6_runner.CASES,
        static_scanner,
    )
    write_json(OUT_ROOT / "reachability_approximation.json", report)
    strengthening_baselines.write_reachability_markdown(OUT_ROOT / "reachability_approximation.md", report)
    return report


def generate_action_boundary_baseline() -> dict[str, Any]:
    report = strengthening_baselines.build_action_boundary_baseline_report(REPO_ROOT, rp6_runner.CASES)
    write_json(OUT_ROOT / "action_boundary_baseline.json", report)
    strengthening_baselines.write_action_boundary_markdown(OUT_ROOT / "action_boundary_baseline.md", report)
    return report


def write_least_privilege_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# Least-Privilege Policy Baseline",
        "",
        report["boundary"],
        "",
        "| Family | Case | Expectation | Passed | Allow Rules | Deny Rules | Expected Outputs |",
        "| --- | --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in report["cases"]:
        shape = row["policy_shape"]
        lines.append(
            "| {family} | {case_id} | `{expectation}` | {passed} | {allow} | {deny} | {outputs} |".format(
                family=row["family"],
                case_id=row["case_id"],
                expectation=row["expectation"],
                passed="yes" if row["expectation_passed"] else "no",
                allow=shape["total_allow_rules"],
                deny=shape["total_deny_rules"],
                outputs=shape["expected_outputs"],
            )
        )
    aggregate = report["aggregate"]
    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            f"- Cases: `{aggregate['case_count']}`",
            f"- Benign expectation passes: `{aggregate['benign_expectation_passes']}/{aggregate['benign_cases']}`",
            f"- Adversarial expectation passes: `{aggregate['adversarial_expectation_passes']}/{aggregate['adversarial_cases']}`",
            f"- Unique contracts: `{aggregate['unique_contracts']}`",
            "",
        ]
    )
    (OUT_ROOT / "least_privilege_baseline.md").write_text("\n".join(lines), encoding="utf-8")


def generate_mitigation_ladder() -> dict[str, Any]:
    rp6_cases = rp6_case_map()
    rows = []
    runtime_aggregates = {
        runtime: {
            "attempted_overreach": 0,
            "canary_observations": 0,
            "event_count": 0,
            "missing_expected_outputs": 0,
            "realized_contract_violations": 0,
        }
        for runtime in ("RP2", "RP3", "RP6")
    }

    for case in rp6_runner.CASES:
        key = (case["family"], case["case_id"])
        runtime_summaries: dict[str, dict[str, Any]] = {}
        for runtime in ("RP2", "RP3"):
            findings = load_json(mvp_findings_path(case, runtime))
            runtime_summaries[runtime] = findings["summary"]
        runtime_summaries["RP6"] = rp6_cases[key]["summary"]
        for runtime, summary in runtime_summaries.items():
            runtime_aggregates[runtime]["attempted_overreach"] += summary["attempted_overreach"]
            runtime_aggregates[runtime]["canary_observations"] += summary["canary_observation_count"]
            runtime_aggregates[runtime]["event_count"] += summary["event_count"]
            runtime_aggregates[runtime]["missing_expected_outputs"] += summary["missing_expected_outputs"]
            runtime_aggregates[runtime]["realized_contract_violations"] += summary["realized_contract_violations"]
        rows.append(
            {
                "case_id": case["case_id"],
                "family": case["family"],
                "is_benign": is_benign(case),
                "runtime_summaries": runtime_summaries,
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
    report = {
        "schema_version": "0.1",
        "report_type": "coarse_mitigation_ladder",
        "boundary": (
            "Coarse observed mitigation ladder using existing RP2, RP3, and RP6 outputs. "
            "This is not a component-level RP6 ablation or defense-success claim."
        ),
        "aggregate": aggregate,
        "cases": rows,
    }
    write_json(OUT_ROOT / "rp6_mitigation_ladder.json", report)
    write_mitigation_ladder_markdown(report)
    return report


def generate_minimal_ablation_matrix() -> dict[str, Any]:
    rp6_cases = rp6_case_map()
    rows = []
    runtime_aggregates = {
        runtime: {
            "attempted_overreach": 0,
            "canary_observations": 0,
            "event_count": 0,
            "missing_expected_outputs": 0,
            "realized_contract_violations": 0,
        }
        for runtime in ("RP2", "RP3", "RP6")
    }
    selected = [
        case for case in rp6_runner.CASES if (case["family"], case["case_id"]) in MINIMAL_ABLATION_CASES
    ]
    rp6_pair_total = 0
    rp6_mitigation_pair_total = 0
    for case in selected:
        key = (case["family"], case["case_id"])
        comparison_path = (
            REPO_ROOT
            / "results"
            / "fixtures"
            / "rp6-policy-hardened"
            / case["family"]
            / f"{case['case_id']}_rp2_rp3_rp6_comparison.json"
        )
        comparison = load_json(comparison_path)
        rp6_pairs = [
            pair
            for pair in comparison["pairs"]
            if "RP6" in {pair["left_runtime_profile"], pair["right_runtime_profile"]}
        ]
        rp6_mitigation_pair_count = sum(
            1
            for pair in rp6_pairs
            if pair["classification"]["claim"] == "mitigation_report_card_comparison"
        )
        if not rp6_pairs:
            raise ValueError(f"{comparison_path}: expected at least one RP6-involved comparison pair")
        if rp6_mitigation_pair_count != len(rp6_pairs):
            raise ValueError(f"{comparison_path}: expected all RP6-involved pairs to be mitigation comparisons")
        rp6_pair_total += len(rp6_pairs)
        rp6_mitigation_pair_total += rp6_mitigation_pair_count
        runtime_summaries: dict[str, dict[str, Any]] = {}
        for runtime in ("RP2", "RP3"):
            runtime_summaries[runtime] = load_json(mvp_findings_path(case, runtime))["summary"]
        runtime_summaries["RP6"] = rp6_cases[key]["summary"]
        for runtime, summary in runtime_summaries.items():
            runtime_aggregates[runtime]["attempted_overreach"] += summary["attempted_overreach"]
            runtime_aggregates[runtime]["canary_observations"] += summary["canary_observation_count"]
            runtime_aggregates[runtime]["event_count"] += summary["event_count"]
            runtime_aggregates[runtime]["missing_expected_outputs"] += summary["missing_expected_outputs"]
            runtime_aggregates[runtime]["realized_contract_violations"] += summary["realized_contract_violations"]
        rows.append(
            {
                "case_id": case["case_id"],
                "comparison_path": display_path(comparison_path),
                "family": case["family"],
                "rp6_mitigation_pair_count": rp6_mitigation_pair_count,
                "rp6_pair_count": len(rp6_pairs),
                "rp6_pairs_are_mitigation_only": True,
                "runtime_summaries": runtime_summaries,
                "variant_id": case["variant_id"],
            }
        )

    policy_probe = load_json(RP6_REPORT_CARD)["policy_probes"][0]
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
    report = {
        "schema_version": "0.1",
        "report_type": "minimal_rp6_report_card_contrast",
        "boundary": (
            "Minimal selected RP6 contrast matrix over fixed existing variants. "
            "This is not a component-level ablation or causal mitigation claim."
        ),
        "aggregate": aggregate,
        "cases": rows,
        "policy_probe": policy_probe,
    }
    write_json(RP6_ABLATION_ROOT / "minimal_report_card.json", report)
    write_minimal_ablation_markdown(report)
    write_minimal_ablation_csv(report)
    return report


def write_minimal_ablation_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# Minimal RP6 Report-Card Contrast",
        "",
        report["boundary"],
        "",
        "| Runtime | Realized Violations | Attempted Overreach | Missing Outputs | Canary Observations |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for runtime in report["aggregate"]["runtime_profiles"]:
        summary = report["aggregate"]["runtime_aggregates"][runtime]
        lines.append(
            "| {runtime} | {realized} | {attempted} | {missing} | {canary} |".format(
                runtime=runtime,
                realized=summary["realized_contract_violations"],
                attempted=summary["attempted_overreach"],
                missing=summary["missing_expected_outputs"],
                canary=summary["canary_observations"],
            )
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Selected variants cover filesystem read/data-flow, network egress, tool/persistence semantics, and filesystem write/output scope.",
            "- AuditLens remains confirmatory coverage in the full RP6 report card, not part of this minimal matrix.",
            f"- RP6-involved pairs checked: `{report['aggregate']['rp6_pair_count']}`.",
            "- RP6-involved pairs remain mitigation contrasts, not runtime-drift claims.",
            "",
        ]
    )
    (RP6_ABLATION_ROOT / "minimal_report_card.md").write_text("\n".join(lines), encoding="utf-8")


def write_minimal_ablation_csv(report: dict[str, Any]) -> None:
    lines = [
        "family,case_id,runtime,realized_contract_violations,attempted_overreach,missing_expected_outputs,canary_observation_count"
    ]
    for row in report["cases"]:
        for runtime in report["aggregate"]["runtime_profiles"]:
            summary = row["runtime_summaries"][runtime]
            lines.append(
                "{family},{case_id},{runtime},{realized},{attempted},{missing},{canary}".format(
                    family=row["family"],
                    case_id=row["case_id"],
                    runtime=runtime,
                    realized=summary["realized_contract_violations"],
                    attempted=summary["attempted_overreach"],
                    missing=summary["missing_expected_outputs"],
                    canary=summary["canary_observation_count"],
                )
            )
    (RP6_ABLATION_ROOT / "minimal_matrix.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_mitigation_ladder_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# RP6 Coarse Mitigation Ladder",
        "",
        report["boundary"],
        "",
        "| Runtime | Realized Violations | Attempted Overreach | Missing Outputs | Canary Observations |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for runtime in report["aggregate"]["runtime_profiles"]:
        summary = report["aggregate"]["runtime_aggregates"][runtime]
        lines.append(
            "| {runtime} | {realized} | {attempted} | {missing} | {canary} |".format(
                runtime=runtime,
                realized=summary["realized_contract_violations"],
                attempted=summary["attempted_overreach"],
                missing=summary["missing_expected_outputs"],
                canary=summary["canary_observations"],
            )
        )
    aggregate = report["aggregate"]
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            f"- RP2 to RP6 realized-violation reduction: `{aggregate['rp2_to_rp6_realized_reduction']}`",
            f"- RP2 to RP6 canary-observation reduction: `{aggregate['rp2_to_rp6_canary_reduction']}`",
            f"- RP6 missing-output increase vs RP2: `{aggregate['rp6_missing_output_increase_vs_rp2']}`",
            "- Interpret the missing-output increase as utility cost, not automatic success.",
            "",
        ]
    )
    (OUT_ROOT / "rp6_mitigation_ladder.md").write_text("\n".join(lines), encoding="utf-8")


def run_json(args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if completed.returncode not in {0, 2}:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(args)}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"command produced no JSON output: {' '.join(args)}\nSTDERR:\n{completed.stderr}")
    return json.loads(lines[-1])


def run_text(args: list[str]) -> None:
    completed = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(args)}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    print(completed.stdout, end="")


def rp6_runner_cases_by_key() -> dict[tuple[str, str], dict[str, Any]]:
    return {(case["family"], case["case_id"]): case for case in rp6_runner.CASES}


def component_profile_path(component_id: str, disabled_components: list[str]) -> Path:
    profile = yaml.safe_load(rp6_runner.RP6_PROFILE.read_text(encoding="utf-8"))
    metadata = dict(profile.get("metadata") or {})
    metadata["rp6_component_ablation"] = {
        "component_id": component_id,
        "disabled_components": disabled_components,
        "generated_by": "tools/run_strengthening_evidence.py",
        "boundary": "controlled RP6 component ablation for research evidence only",
    }
    profile["metadata"] = metadata
    profile["profile_version"] = f"{profile.get('profile_version', '0.1')}-ablation-{component_id}"
    profile["description"] = (
        f"{profile.get('description', '').rstrip()} Component ablation profile for {component_id}; "
        "not used for normal RP6 report-card counts."
    )
    profile.setdefault("notes", [])
    profile["notes"] = list(profile["notes"]) + [
        f"Generated component-ablation profile with disabled controls: {', '.join(disabled_components)}."
    ]
    profile_path = COMPONENT_ABLATION_INPUT_ROOT / "profiles" / f"RP6_ablate_{component_id}.yaml"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")
    return profile_path


def component_case_spec(ref: dict[str, Any]) -> dict[str, Any]:
    if ref["case_id"] == "network_policy_probe":
        return {
            "family": "network-egress",
            "case_id": "network_policy_probe",
            "contract": "contracts/network-egress-executable-smoke.yaml",
            "workspace": "benchmark/workspaces/network-egress-smoke",
            "variant_id": "network-egress-smoke.rp6-network-policy-probe",
            "command": ["python3", "-c", rp6_runner.NETWORK_POLICY_PROBE_SCRIPT],
        }
    return dict(rp6_runner_cases_by_key()[(ref["family"], ref["case_id"])])


def component_baseline_row(ref: dict[str, Any], rp6_cases: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    if ref["case_id"] == "network_policy_probe":
        report = load_json(RP6_REPORT_CARD)
        return report["policy_probes"][0]
    return rp6_cases[(ref["family"], ref["case_id"])]


def annotate_component_findings(
    path: Path,
    *,
    component_id: str,
    disabled_components: list[str],
    baseline_summary: dict[str, Any],
) -> dict[str, Any]:
    findings = load_json(path)
    findings["comparison_role"] = "rp6_component_ablation"
    findings["component_id"] = component_id
    findings["disabled_components"] = disabled_components
    findings["baseline_summary"] = baseline_summary
    path.write_text(json.dumps(findings, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return findings


def summary_delta(baseline: dict[str, Any], ablated: dict[str, Any]) -> dict[str, int]:
    return {
        field: int(ablated.get(field, 0)) - int(baseline.get(field, 0))
        for field in COMPONENT_SUMMARY_FIELDS
    }


def utility_preserved(summary: dict[str, Any]) -> bool:
    return (
        summary.get("trace_valid") is True
        and summary.get("missing_expected_outputs") == 0
        and summary.get("output_oracle_failures") == 0
    )


def security_regression_observed(delta: dict[str, int]) -> bool:
    return (
        delta["realized_contract_violations"] > 0
        or delta["canary_observation_count"] > 0
        or (delta["attempted_overreach"] < 0 and delta["realized_contract_violations"] > 0)
    )


def run_component_ablation_case(
    *,
    component_id: str,
    component_name: str,
    disabled_components: list[str],
    profile_path: Path,
    ref: dict[str, Any],
    rp6_cases: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    case = component_case_spec(ref)
    baseline = component_baseline_row(ref, rp6_cases)
    family = case["family"]
    case_id = case["case_id"]
    contract = REPO_ROOT / case["contract"]
    workspace = REPO_ROOT / case["workspace"]
    variant_id = f"{case['variant_id']}.rp6_component_ablation.{component_id}"
    result = run_json(
        [
            PYTHON,
            "tools/skilldiff.py",
            "run",
            "--profile",
            str(profile_path),
            "--contract",
            str(contract),
            "--workspace",
            str(workspace),
            "--workspace-seed-id",
            f"{family}-{case_id}-rp6-component-ablation-{component_id}",
            "--variant-id",
            variant_id,
            "--output-root",
            str(COMPONENT_ABLATION_RUN_ROOT),
            "--repeat-id",
            "1",
            "--live",
            "--command",
            *case["command"],
        ]
    )
    component_dir = RP6_ABLATION_ROOT / "components" / component_id
    component_dir.mkdir(parents=True, exist_ok=True)
    safe_case_id = case_id.replace("/", "_")
    findings_path = component_dir / f"{family}_{safe_case_id}_component_findings.json"
    run_text(
        [
            PYTHON,
            "tools/check_contract.py",
            "--contract",
            str(contract),
            "--trace",
            result["trace_path"],
            "--out-json",
            str(findings_path),
            "--out-md",
            str(component_dir / f"{family}_{safe_case_id}_component_report.md"),
        ]
    )
    findings = annotate_component_findings(
        findings_path,
        component_id=component_id,
        disabled_components=disabled_components,
        baseline_summary=baseline["summary"],
    )
    delta = summary_delta(baseline["summary"], findings["summary"])
    role = ref["case_role"]
    row_utility_preserved = utility_preserved(findings["summary"])
    row_security_regression = security_regression_observed(delta)
    expectation_passed = row_utility_preserved if role == "benign_control" else row_security_regression
    return {
        "ablated_findings_path": display_path(findings_path),
        "ablated_summary": findings["summary"],
        "ablated_trace_path": display_path(Path(result["trace_path"])),
        "adapter_outcome": result["adapter_outcome"],
        "baseline_findings_path": baseline["findings_path"],
        "baseline_summary": baseline["summary"],
        "baseline_trace_path": baseline["trace_path"],
        "case_id": case_id,
        "case_role": role,
        "command": case["command"] if case_id != "network_policy_probe" else ["python3", "-c", "<inline RP6 network policy probe>"],
        "component_id": component_id,
        "component_name": component_name,
        "contract": case["contract"],
        "delta": delta,
        "disabled_components": disabled_components,
        "expectation": "utility_preserved" if role == "benign_control" else "security_regression_observed",
        "expectation_passed": expectation_passed,
        "exit_code": result["exit_code"],
        "family": family,
        "runtime_profile": findings["runtime_profile"],
        "security_regression_observed": row_security_regression,
        "utility_preserved": row_utility_preserved,
        "variant_id": variant_id,
    }


def component_aggregate(rows: list[dict[str, Any]], components: list[dict[str, Any]]) -> dict[str, Any]:
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


def generate_component_ablation_report() -> dict[str, Any]:
    if COMPONENT_ABLATION_RUN_ROOT.exists():
        shutil.rmtree(COMPONENT_ABLATION_RUN_ROOT)
    if COMPONENT_ABLATION_INPUT_ROOT.exists():
        shutil.rmtree(COMPONENT_ABLATION_INPUT_ROOT)
    component_outputs = RP6_ABLATION_ROOT / "components"
    if component_outputs.exists():
        shutil.rmtree(component_outputs)
    COMPONENT_ABLATION_RUN_ROOT.mkdir(parents=True, exist_ok=True)

    rp6_cases = rp6_case_map()
    rows = []
    components = []
    for component in COMPONENT_ABLATIONS:
        profile_path = component_profile_path(component["component_id"], component["disabled_components"])
        component_rows = [
            run_component_ablation_case(
                component_id=component["component_id"],
                component_name=component["component_name"],
                disabled_components=component["disabled_components"],
                profile_path=profile_path,
                ref=ref,
                rp6_cases=rp6_cases,
            )
            for ref in component["cases"]
        ]
        rows.extend(component_rows)
        components.append(
            {
                "component_id": component["component_id"],
                "component_name": component["component_name"],
                "disabled_components": component["disabled_components"],
                "profile_path": display_path(profile_path),
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

    report = {
        "schema_version": "0.1",
        "report_type": "rp6_component_ablation",
        "boundary": (
            "Controlled RP6 component-ablation evidence over fixture commands. "
            "Each row disables one named RP6 control in a generated ablation profile and checks the resulting trace "
            "against the original contract. This is excluded from RP2/RP3 MVP drift counts and is not a commercial "
            "runtime, Semia-equivalence, public-network, defense-success, or statistical claim."
        ),
        "claim_boundary": {
            "commercial_runtime_claim": False,
            "defense_success_claim": False,
            "public_network_claim": False,
            "semia_equivalence_claim": False,
            "statistical_claim": False,
        },
        "aggregate": component_aggregate(rows, components),
        "components": components,
        "cases": rows,
    }
    write_json(RP6_ABLATION_ROOT / "component_report_card.json", report)
    write_component_ablation_markdown(report)
    write_component_ablation_csv(report)
    return report


def write_component_ablation_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# RP6 Component Ablation Report Card",
        "",
        report["boundary"],
        "",
        "| Component | Cases | Expected Rows Passed | Security Regressions | Utility Preserved | Realized Delta | Canary Delta |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for component in report["components"]:
        lines.append(
            "| {component} | {cases} | {passed} | {security} | {utility} | {realized} | {canary} |".format(
                component=component["component_id"],
                cases=component["case_count"],
                passed=component["expectation_passed_cases"],
                security=component["security_regression_cases"],
                utility=component["utility_preserved_cases"],
                realized=component["realized_contract_violation_delta"],
                canary=component["canary_observation_delta"],
            )
        )
    aggregate = report["aggregate"]
    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            f"- Components: `{aggregate['component_count']}`",
            f"- Cases: `{aggregate['case_count']}`",
            f"- Components with benign and adversarial/probe coverage: `{aggregate['components_with_benign_and_adversarial_coverage']}`",
            f"- Expectation-passed rows: `{aggregate['expectation_passed_cases']}`",
            f"- Security-regression rows: `{aggregate['security_regression_cases']}`",
            f"- Utility-preserved rows: `{aggregate['utility_preserved_cases']}`",
            f"- Realized contract-violation delta: `{aggregate['realized_contract_violation_delta']}`",
            f"- Canary-observation delta: `{aggregate['canary_observation_delta']}`",
            "",
            "## Boundary",
            "",
            "- Generated profiles are fixture-only ablations; normal RP6 report-card runs keep all controls enabled.",
            "- Network ablation records a synthetic allowed fake-sink response and does not contact public internet.",
            "- The artifact supports component-associated evidence, not a broad defense-success or product-sandbox claim.",
            "",
        ]
    )
    (RP6_ABLATION_ROOT / "component_report_card.md").write_text("\n".join(lines), encoding="utf-8")


def write_component_ablation_csv(report: dict[str, Any]) -> None:
    lines = [
        "component_id,family,case_id,case_role,expectation_passed,utility_preserved,security_regression_observed,baseline_realized,ablated_realized,baseline_canary,ablated_canary,baseline_missing_outputs,ablated_missing_outputs"
    ]
    for row in report["cases"]:
        lines.append(
            "{component},{family},{case_id},{case_role},{expectation},{utility},{security},{base_realized},{abl_realized},{base_canary},{abl_canary},{base_missing},{abl_missing}".format(
                component=row["component_id"],
                family=row["family"],
                case_id=row["case_id"],
                case_role=row["case_role"],
                expectation=str(row["expectation_passed"]).lower(),
                utility=str(row["utility_preserved"]).lower(),
                security=str(row["security_regression_observed"]).lower(),
                base_realized=row["baseline_summary"]["realized_contract_violations"],
                abl_realized=row["ablated_summary"]["realized_contract_violations"],
                base_canary=row["baseline_summary"]["canary_observation_count"],
                abl_canary=row["ablated_summary"]["canary_observation_count"],
                base_missing=row["baseline_summary"]["missing_expected_outputs"],
                abl_missing=row["ablated_summary"]["missing_expected_outputs"],
            )
        )
    (RP6_ABLATION_ROOT / "component_matrix.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def summary_without_event_count(summary: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in summary.items() if key != "event_count"}


def build_repeat_observation(
    *,
    repeat_id: str,
    source: str,
    findings_path: Path | str,
    trace_path: Path | str,
    summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "findings_path": display_path(Path(findings_path)),
        "repeat_id": repeat_id,
        "source": source,
        "summary": summary,
        "summary_without_event_count": summary_without_event_count(summary),
        "trace_path": display_path(Path(trace_path)),
    }


def run_repeat_case(case: dict[str, Any], repeat_id: str) -> dict[str, Any]:
    family = case["family"]
    case_id = case["case_id"]
    contract = REPO_ROOT / case["contract"]
    workspace = REPO_ROOT / case["workspace"]
    result = run_json(
        [
            PYTHON,
            "tools/skilldiff.py",
            "run",
            "--profile",
            str(rp6_runner.RP6_PROFILE),
            "--contract",
            str(contract),
            "--workspace",
            str(workspace),
            "--workspace-seed-id",
            f"{family}-{case_id}-rp6-repeat-stability",
            "--variant-id",
            case["variant_id"],
            "--output-root",
            str(REPEAT_RUN_ROOT),
            "--repeat-id",
            repeat_id,
            "--live",
            "--command",
            *case["command"],
        ]
    )
    family_dir = REPEAT_ROOT / family
    family_dir.mkdir(parents=True, exist_ok=True)
    repeat_findings = family_dir / f"{case_id}_repeat{repeat_id}_contract_findings.json"
    run_text(
        [
            PYTHON,
            "tools/check_contract.py",
            "--contract",
            str(contract),
            "--trace",
            result["trace_path"],
            "--out-json",
            str(repeat_findings),
            "--out-md",
            str(family_dir / f"{case_id}_repeat{repeat_id}_contract_report.md"),
        ]
    )
    findings = load_json(repeat_findings)
    return build_repeat_observation(
        repeat_id=repeat_id,
        source="strengthening_repeat",
        findings_path=repeat_findings,
        trace_path=result["trace_path"],
        summary=findings["summary"],
    )


def generate_repeat_stability() -> dict[str, Any]:
    if REPEAT_ROOT.exists():
        shutil.rmtree(REPEAT_ROOT)
    REPEAT_RUN_ROOT.mkdir(parents=True, exist_ok=True)

    rp6_cases = rp6_case_map()
    rows = []
    for case in rp6_runner.CASES:
        family = case["family"]
        case_id = case["case_id"]
        first_case = rp6_cases[(family, case_id)]
        observations = [
            build_repeat_observation(
                repeat_id="1",
                source="rp6_report_card",
                findings_path=first_case["findings_path"],
                trace_path=first_case["trace_path"],
                summary=first_case["summary"],
            )
        ]
        observations.extend(run_repeat_case(case, repeat_id) for repeat_id in GENERATED_REPEAT_IDS)
        first_summary = observations[0]["summary"]
        first_comparable_summary = observations[0]["summary_without_event_count"]
        stable_excluding_event_count = all(
            observation["summary_without_event_count"] == first_comparable_summary
            for observation in observations
        )
        stable_including_event_count = all(
            observation["summary"] == first_summary
            for observation in observations
        )
        rows.append(
            {
                "case_id": case_id,
                "family": family,
                "observation_count": len(observations),
                "observations": observations,
                "repeat_ids": list(STABILITY_REPEAT_IDS),
                "stable_summary_excluding_event_count": stable_excluding_event_count,
                "stable_summary_including_event_count": stable_including_event_count,
                "variant_id": case["variant_id"],
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
        "repeat_ids": list(STABILITY_REPEAT_IDS),
        "repeat_observation_count": len(observations),
        "repeats_per_case": len(STABILITY_REPEAT_IDS),
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
    report = {
        "schema_version": "0.1",
        "report_type": "rp6_repeat_stability",
        "boundary": (
            "Bounded deterministic RP6 repeat-stability check over current controlled fixtures. "
            "It is not a prevalence, statistical, or model-mediated stability claim."
        ),
        "aggregate": aggregate,
        "cases": rows,
    }
    write_json(REPEAT_ROOT / "repeat_stability.json", report)
    write_repeat_stability_markdown(report)
    return report


def write_repeat_stability_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# RP6 Repeat Stability",
        "",
        report["boundary"],
        "",
        "| Family | Case | Repeats | Stable Outcome | Realized Across Repeats | Canary Across Repeats | Traces |",
        "| --- | --- | ---: | --- | ---: | ---: | --- |",
    ]
    for row in report["cases"]:
        realized = sum(
            observation["summary"]["realized_contract_violations"]
            for observation in row["observations"]
        )
        canary = sum(
            observation["summary"]["canary_observation_count"]
            for observation in row["observations"]
        )
        trace_refs = "<br>".join(f"`{observation['trace_path']}`" for observation in row["observations"])
        lines.append(
            "| {family} | {case_id} | {repeats} | {stable} | {realized} | {canary} | {traces} |".format(
                family=row["family"],
                case_id=row["case_id"],
                repeats=row["observation_count"],
                stable="yes" if row["stable_summary_excluding_event_count"] else "no",
                realized=realized,
                canary=canary,
                traces=trace_refs,
            )
        )
    aggregate = report["aggregate"]
    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            f"- Cases: `{aggregate['case_count']}`",
            f"- Repeat observations: `{aggregate['repeat_observation_count']}`",
            f"- Repeat IDs: `{', '.join(aggregate['repeat_ids'])}`",
            f"- Bounded deterministic stability claims supported: `{aggregate['deterministic_stability_claims_supported']}`",
            f"- Matching summaries excluding event count: `{aggregate['summary_match_count_excluding_event_count']}`",
            f"- Matching summaries including event count: `{aggregate['summary_match_count_including_event_count']}`",
            f"- Trace-valid repeats: `{aggregate['trace_valid_count']}`",
            f"- Statistical repeat-stability claims supported: `{aggregate['statistical_repeat_stability_claims_supported']}`",
            "",
        ]
    )
    (REPEAT_ROOT / "repeat_stability.md").write_text("\n".join(lines), encoding="utf-8")


def write_index(reports: dict[str, dict[str, Any]]) -> None:
    index = {
        "schema_version": "0.1",
        "report_type": "strengthening_evidence_index",
        "reports": {
            "action_boundary_baseline": "results/fixtures/strengthening/action_boundary_baseline.json",
            "least_privilege_baseline": "results/fixtures/strengthening/least_privilege_baseline.json",
            "reachability_approximation": "results/fixtures/strengthening/reachability_approximation.json",
            "rp6_mitigation_ladder": "results/fixtures/strengthening/rp6_mitigation_ladder.json",
            "rp6_component_ablation": "results/fixtures/rp6-policy-hardened/ablations/component_report_card.json",
            "rp6_minimal_report_card_contrast": "results/fixtures/rp6-policy-hardened/ablations/minimal_report_card.json",
            "rp6_repeat_stability": "results/fixtures/strengthening/repeat-stability/repeat_stability.json",
            "static_scanner_baseline": "results/fixtures/strengthening/static_scanner_baseline.json",
        },
        "aggregates": {key: value["aggregate"] for key, value in reports.items()},
        "boundary": (
            "Strengthening package for reviewer-facing baselines. These artifacts are excluded from MVP runtime-drift counts."
        ),
    }
    write_json(OUT_ROOT / "index.json", index)
    lines = [
        "# Strengthening Evidence Index",
        "",
        index["boundary"],
        "",
        "| Artifact | Path |",
        "| --- | --- |",
    ]
    for key, path in index["reports"].items():
        lines.append(f"| `{key}` | `{path}` |")
    lines.append("")
    (OUT_ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baselines-only",
        action="store_true",
        help="Regenerate only static/reachability/action-boundary baselines and refresh the index.",
    )
    args = parser.parse_args(argv)
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    static_scanner = generate_static_scanner_baseline()
    reachability = generate_reachability_approximation(static_scanner)
    action_boundary = generate_action_boundary_baseline()
    if args.baselines_only:
        existing_reports = {
            "least_privilege_baseline": load_json(OUT_ROOT / "least_privilege_baseline.json"),
            "rp6_mitigation_ladder": load_json(OUT_ROOT / "rp6_mitigation_ladder.json"),
            "rp6_component_ablation": load_json(RP6_ABLATION_ROOT / "component_report_card.json"),
            "rp6_minimal_report_card_contrast": load_json(RP6_ABLATION_ROOT / "minimal_report_card.json"),
            "rp6_repeat_stability": load_json(REPEAT_ROOT / "repeat_stability.json"),
        }
        write_index(
            {
                "action_boundary_baseline": action_boundary,
                "least_privilege_baseline": existing_reports["least_privilege_baseline"],
                "reachability_approximation": reachability,
                "rp6_mitigation_ladder": existing_reports["rp6_mitigation_ladder"],
                "rp6_component_ablation": existing_reports["rp6_component_ablation"],
                "rp6_minimal_report_card_contrast": existing_reports["rp6_minimal_report_card_contrast"],
                "rp6_repeat_stability": existing_reports["rp6_repeat_stability"],
                "static_scanner_baseline": static_scanner,
            }
        )
        print(OUT_ROOT / "index.json")
        return 0
    least_privilege = generate_least_privilege_baseline()
    mitigation_ladder = generate_mitigation_ladder()
    minimal_ablation = generate_minimal_ablation_matrix()
    component_ablation = generate_component_ablation_report()
    repeat_stability = generate_repeat_stability()
    write_index(
        {
            "action_boundary_baseline": action_boundary,
            "least_privilege_baseline": least_privilege,
            "reachability_approximation": reachability,
            "rp6_mitigation_ladder": mitigation_ladder,
            "rp6_component_ablation": component_ablation,
            "rp6_minimal_report_card_contrast": minimal_ablation,
            "rp6_repeat_stability": repeat_stability,
            "static_scanner_baseline": static_scanner,
        }
    )
    print(OUT_ROOT / "index.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
