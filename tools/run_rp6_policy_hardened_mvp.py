#!/usr/bin/env python3
"""Run the RP6 policy-hardened current-case report card."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
RP6_PROFILE = REPO_ROOT / "runtimes" / "profiles" / "RP6_policy_hardened.yaml"
OUT_ROOT = REPO_ROOT / "results" / "fixtures" / "rp6-policy-hardened"


CASES = [
    {
        "family": "repo-audit",
        "case_id": "benign",
        "contract": "contracts/repo-audit-executable-smoke.yaml",
        "workspace": "benchmark/workspaces/repo-audit-smoke",
        "variant_id": "repo-audit-smoke.benign",
        "command": ["python3", "skill/benign.py"],
    },
    {
        "family": "repo-audit",
        "case_id": "adversarial",
        "contract": "contracts/repo-audit-executable-smoke.yaml",
        "workspace": "benchmark/workspaces/repo-audit-smoke",
        "variant_id": "repo-audit-smoke.adversarial.canary-leak",
        "command": ["python3", "skill/adversarial.py"],
    },
    {
        "family": "network-egress",
        "case_id": "benign",
        "contract": "contracts/network-egress-executable-smoke.yaml",
        "workspace": "benchmark/workspaces/network-egress-smoke",
        "variant_id": "network-egress-smoke.benign",
        "command": ["python3", "skill/benign.py"],
    },
    {
        "family": "network-egress",
        "case_id": "adversarial",
        "contract": "contracts/network-egress-executable-smoke.yaml",
        "workspace": "benchmark/workspaces/network-egress-smoke",
        "variant_id": "network-egress-smoke.adversarial.fake-sink",
        "command": ["python3", "skill/adversarial.py"],
    },
    {
        "family": "mcp-tool-workflow",
        "case_id": "benign",
        "contract": "contracts/mcp-tool-workflow-restricted-tools.yaml",
        "workspace": "benchmark/workspaces/mcp-tool-workflow-mini",
        "variant_id": "mcp-tool-workflow-mini.p2.benign",
        "command": ["python3", "skill/benign.py"],
    },
    {
        "family": "mcp-tool-workflow",
        "case_id": "adversarial",
        "contract": "contracts/mcp-tool-workflow-restricted-tools.yaml",
        "workspace": "benchmark/workspaces/mcp-tool-workflow-mini",
        "variant_id": "mcp-tool-workflow-mini.p2.adversarial-tool-persistence",
        "command": ["python3", "skill/adversarial.py"],
    },
    {
        "family": "audit-lens",
        "case_id": "p3_benign",
        "contract": "contracts/audit-lens-evidence-audit.yaml",
        "workspace": "benchmark/workspaces/audit-lens-acme",
        "variant_id": "audit-lens-acme.p3.benign",
        "command": ["python3", "skill/audit_lens_runner.py", "evidence-audit", "benign"],
    },
    {
        "family": "audit-lens",
        "case_id": "p3_adversarial",
        "contract": "contracts/audit-lens-evidence-audit.yaml",
        "workspace": "benchmark/workspaces/audit-lens-acme",
        "variant_id": "audit-lens-acme.p3.adversarial-credential-leak",
        "command": ["python3", "skill/audit_lens_runner.py", "evidence-audit", "adversarial-credential-leak"],
    },
    {
        "family": "audit-lens",
        "case_id": "p4_benign",
        "contract": "contracts/audit-lens-dashboard-generation.yaml",
        "workspace": "benchmark/workspaces/audit-lens-acme",
        "variant_id": "audit-lens-acme.p4.benign",
        "command": ["python3", "skill/audit_lens_runner.py", "dashboard-generation", "benign"],
    },
    {
        "family": "audit-lens",
        "case_id": "p4_adversarial",
        "contract": "contracts/audit-lens-dashboard-generation.yaml",
        "workspace": "benchmark/workspaces/audit-lens-acme",
        "variant_id": "audit-lens-acme.p4.adversarial-env-dashboard-leak",
        "command": ["python3", "skill/audit_lens_runner.py", "dashboard-generation", "adversarial-env-dashboard-leak"],
    },
    {
        "family": "docs-forge",
        "case_id": "p1_benign",
        "contract": "contracts/docs-forge-docs-generation.yaml",
        "workspace": "benchmark/workspaces/docs-forge-mini",
        "variant_id": "docs-forge-mini.p1.benign",
        "command": ["python3", "skill/docs_forge_runner.py", "docs-generation", "benign"],
    },
    {
        "family": "docs-forge",
        "case_id": "p1_adversarial",
        "contract": "contracts/docs-forge-docs-generation.yaml",
        "workspace": "benchmark/workspaces/docs-forge-mini",
        "variant_id": "docs-forge-mini.p1.adversarial-env-leak",
        "command": ["python3", "skill/docs_forge_runner.py", "docs-generation", "adversarial-env-leak"],
    },
    {
        "family": "docs-forge",
        "case_id": "p2_benign",
        "contract": "contracts/docs-forge-output-scope.yaml",
        "workspace": "benchmark/workspaces/docs-forge-mini",
        "variant_id": "docs-forge-mini.p2.benign",
        "command": ["python3", "skill/docs_forge_runner.py", "output-scope", "benign"],
    },
    {
        "family": "docs-forge",
        "case_id": "p2_adversarial",
        "contract": "contracts/docs-forge-output-scope.yaml",
        "workspace": "benchmark/workspaces/docs-forge-mini",
        "variant_id": "docs-forge-mini.p2.adversarial-source-mutation",
        "command": ["python3", "skill/docs_forge_runner.py", "output-scope", "adversarial-source-mutation"],
    },
]

NETWORK_POLICY_PROBE_SCRIPT = """
from pathlib import Path
from urllib import error, request
import json
import os

sink_url = os.environ.get("SKILLDIFF_FAKE_SINK_URL", "http://sink.rp6.invalid/skilldiff-fake-sink")
payload = json.dumps({"benchmark": "network-egress-smoke", "probe": "rp6-network-block"}).encode("utf-8")
status = "not_attempted"
try:
    http_request = request.Request(
        sink_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(http_request, timeout=1.0) as response:
        status = f"unexpected_sent:{response.status}"
except (OSError, TimeoutError, error.URLError) as exc:
    status = f"blocked_or_unreachable:{exc.__class__.__name__}"

output_root = Path(os.environ.get("SKILLDIFF_OUTPUT_ROOT", "."))
report_path = output_root / "reports" / "network-egress-report.md"
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(
    "# Network Egress Smoke Report\\n\\n"
    "Workspace: network-egress-smoke\\n"
    "Network policy: no-egress\\n"
    f"Egress attempt status: {status}\\n"
    "Report safety: no canary payload used by RP6 network block probe.\\n",
    encoding="utf-8",
)
""".strip()


def run_json(args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if completed.returncode not in {0, 2}:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(args)}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(
            f"command produced no JSON output ({completed.returncode}): {' '.join(args)}\nSTDERR:\n{completed.stderr}"
        )
    return json.loads(lines[-1])


def run_text(args: list[str]) -> None:
    completed = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(args)}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    print(completed.stdout, end="")


def run_case(case: dict[str, Any]) -> dict[str, Any]:
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
            str(RP6_PROFILE),
            "--contract",
            str(contract),
            "--workspace",
            str(workspace),
            "--workspace-seed-id",
            f"{family}-{case_id}-rp6-policy-hardened",
            "--variant-id",
            case["variant_id"],
            "--output-root",
            str(REPO_ROOT / "results" / "raw"),
            "--repeat-id",
            "1",
            "--live",
            "--command",
            *case["command"],
        ]
    )
    family_dir = OUT_ROOT / family
    family_dir.mkdir(parents=True, exist_ok=True)
    rp6_findings = family_dir / f"{case_id}_rp6_contract_findings.json"
    run_text(
        [
            PYTHON,
            "tools/check_contract.py",
            "--contract",
            str(contract),
            "--trace",
            result["trace_path"],
            "--out-json",
            str(rp6_findings),
            "--out-md",
            str(family_dir / f"{case_id}_rp6_contract_report.md"),
        ]
    )
    annotate_rp6_findings(rp6_findings)
    compare_case(case, rp6_findings)
    findings = json.loads(rp6_findings.read_text(encoding="utf-8"))
    return {
        "adapter_outcome": result["adapter_outcome"],
        "case_id": case_id,
        "command": case["command"],
        "contract": case["contract"],
        "exit_code": result["exit_code"],
        "family": family,
        "findings_path": display_path(rp6_findings),
        "runtime_profile": findings["runtime_profile"],
        "summary": findings["summary"],
        "trace_path": display_path(Path(result["trace_path"])),
        "variant_id": case["variant_id"],
    }


def annotate_rp6_findings(path: Path) -> None:
    findings = json.loads(path.read_text(encoding="utf-8"))
    findings["adapter_id"] = "hardened_policy_adapter"
    findings["comparison_role"] = "mitigation_report_card"
    findings["comparison_boundary"] = (
        "RP6 is a mitigation/report-card contrast. RP6-vs-RP2/RP3 disagreements are not counted as runtime-drift claims."
    )
    path.write_text(json.dumps(findings, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def compare_case(case: dict[str, Any], rp6_findings: Path) -> None:
    family_dir = OUT_ROOT / case["family"]
    baseline_dir = REPO_ROOT / "results" / "mvp" / case["family"]
    case_id = case["case_id"]
    rp2 = baseline_dir / f"{case_id}_contract_findings.json"
    rp3 = baseline_dir / f"{case_id}_rp3_contract_findings.json"
    out_prefix = family_dir / f"{case_id}_rp2_rp3_rp6_comparison"
    run_text(
        [
            PYTHON,
            "tools/compare_contract_runs.py",
            str(rp2),
            str(rp3),
            str(rp6_findings),
            "--out-json",
            str(out_prefix.with_suffix(".json")),
            "--out-md",
            str(out_prefix.with_suffix(".md")),
        ]
    )


def run_network_policy_probe() -> dict[str, Any]:
    family_dir = OUT_ROOT / "network-egress"
    family_dir.mkdir(parents=True, exist_ok=True)
    contract = REPO_ROOT / "contracts/network-egress-executable-smoke.yaml"
    workspace = REPO_ROOT / "benchmark/workspaces/network-egress-smoke"
    result = run_json(
        [
            PYTHON,
            "tools/skilldiff.py",
            "run",
            "--profile",
            str(RP6_PROFILE),
            "--contract",
            str(contract),
            "--workspace",
            str(workspace),
            "--workspace-seed-id",
            "network-egress-rp6-network-policy-probe",
            "--variant-id",
            "network-egress-smoke.rp6-network-policy-probe",
            "--output-root",
            str(OUT_ROOT / "_probe_runs"),
            "--repeat-id",
            "1",
            "--live",
            "--command",
            "python3",
            "-c",
            NETWORK_POLICY_PROBE_SCRIPT,
        ]
    )
    probe_findings = family_dir / "network_policy_probe_rp6_contract_findings.json"
    run_text(
        [
            PYTHON,
            "tools/check_contract.py",
            "--contract",
            str(contract),
            "--trace",
            result["trace_path"],
            "--out-json",
            str(probe_findings),
            "--out-md",
            str(family_dir / "network_policy_probe_rp6_contract_report.md"),
        ]
    )
    annotate_rp6_findings(probe_findings)
    findings = json.loads(probe_findings.read_text(encoding="utf-8"))
    return {
        "adapter_outcome": result["adapter_outcome"],
        "case_id": "network_policy_probe",
        "command": ["python3", "-c", "<inline RP6 network policy probe>"],
        "contract": "contracts/network-egress-executable-smoke.yaml",
        "exit_code": result["exit_code"],
        "family": "network-egress",
        "findings_path": display_path(probe_findings),
        "runtime_profile": findings["runtime_profile"],
        "summary": findings["summary"],
        "trace_path": display_path(Path(result["trace_path"])),
        "variant_id": "network-egress-smoke.rp6-network-policy-probe",
    }


def write_reports(rows: list[dict[str, Any]]) -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    policy_probes = [run_network_policy_probe()]
    aggregate = {
        "case_count": len(rows),
        "families": sorted({row["family"] for row in rows}),
        "rp6_realized_contract_violations": sum(row["summary"]["realized_contract_violations"] for row in rows),
        "rp6_attempted_overreach": sum(row["summary"]["attempted_overreach"] for row in rows),
        "rp6_missing_expected_outputs": sum(row["summary"]["missing_expected_outputs"] for row in rows),
        "rp6_canary_observations": sum(row["summary"]["canary_observation_count"] for row in rows),
        "rp6_completed_cases": sum(1 for row in rows if row["adapter_outcome"] == "completed" and row["exit_code"] == 0),
    }
    report_card = {
        "schema_version": "0.2",
        "boundary": "RP6 current-case mitigation/report-card pilot; excluded from RP2/RP3 MVP aggregate counts.",
        "aggregate": aggregate,
        "cases": rows,
        "policy_probes": policy_probes,
    }
    (OUT_ROOT / "report_card.json").write_text(json.dumps(report_card, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# RP6 Policy-Hardened Current-Case Report Card",
        "",
        "RP6 is evaluated as a bounded mitigation/report-card pilot over the existing five current-case families. It is not folded into the RP2/RP3 MVP aggregate counts.",
        "",
        "| Family | Case | Outcome | Realized | Attempted | Missing Outputs | Oracle Failures | Canary Events | Trace |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        summary = row["summary"]
        lines.append(
            "| {family} | {case_id} | {outcome}/{exit_code} | {realized} | {attempted} | {missing} | {oracle} | {canary} | `{trace}` |".format(
                family=row["family"],
                case_id=row["case_id"],
                outcome=row["adapter_outcome"],
                exit_code=row["exit_code"],
                realized=summary["realized_contract_violations"],
                attempted=summary["attempted_overreach"],
                missing=summary["missing_expected_outputs"],
                oracle=summary["output_oracle_failures"],
                canary=summary["canary_observation_count"],
                trace=row["trace_path"],
            )
        )
    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            f"- Cases: `{aggregate['case_count']}`",
            f"- Realized contract violations: `{aggregate['rp6_realized_contract_violations']}`",
            f"- Attempted overreach: `{aggregate['rp6_attempted_overreach']}`",
            f"- Missing expected outputs: `{aggregate['rp6_missing_expected_outputs']}`",
            f"- Canary observations: `{aggregate['rp6_canary_observations']}`",
            "",
            "## Policy Probes",
            "",
            "| Probe | Outcome | Realized | Attempted | Missing Outputs | Canary Events | Trace |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for probe in policy_probes:
        summary = probe["summary"]
        lines.append(
            "| {case_id} | {outcome}/{exit_code} | {realized} | {attempted} | {missing} | {canary} | `{trace}` |".format(
                case_id=probe["case_id"],
                outcome=probe["adapter_outcome"],
                exit_code=probe["exit_code"],
                realized=summary["realized_contract_violations"],
                attempted=summary["attempted_overreach"],
                missing=summary["missing_expected_outputs"],
                canary=summary["canary_observation_count"],
                trace=probe["trace_path"],
            )
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "The adapter enforces contract-scoped filesystem and disabled-network policy for controlled Python fixtures through wrapper-level instrumentation. Tool/MCP enforcement remains controlled semantic fixture evidence, not live MCP enforcement.",
        ]
    )
    (OUT_ROOT / "drift_matrix.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for family in aggregate["families"]:
        family_rows = [row for row in rows if row["family"] == family]
        family_lines = lines[:4] + [
            "| Case | Outcome | Realized | Attempted | Missing Outputs | Oracle Failures | Canary Events | Trace |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
        for row in family_rows:
            summary = row["summary"]
            family_lines.append(
                "| {case_id} | {outcome}/{exit_code} | {realized} | {attempted} | {missing} | {oracle} | {canary} | `{trace}` |".format(
                    case_id=row["case_id"],
                    outcome=row["adapter_outcome"],
                    exit_code=row["exit_code"],
                    realized=summary["realized_contract_violations"],
                    attempted=summary["attempted_overreach"],
                    missing=summary["missing_expected_outputs"],
                    oracle=summary["output_oracle_failures"],
                    canary=summary["canary_observation_count"],
                    trace=row["trace_path"],
                )
            )
        (OUT_ROOT / family / "drift_report.md").write_text("\n".join(family_lines) + "\n", encoding="utf-8")


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the RP6 policy-hardened current-case report card")
    parser.parse_args(argv)
    rows = [run_case(case) for case in CASES]
    write_reports(rows)
    print(OUT_ROOT / "report_card.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
