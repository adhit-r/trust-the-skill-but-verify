#!/usr/bin/env python3
"""Run the RP1 restricted-hosted current-subset scaffold."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit("PyYAML is required to run the RP1 scaffold") from exc


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
RP1_PROFILE = REPO_ROOT / "runtimes" / "profiles" / "RP1_restricted_hosted.yaml"
MANIFEST = REPO_ROOT / "benchmark" / "manifests" / "rp1-restricted-hosted-mvp.json"
OUT_ROOT = REPO_ROOT / "results" / "fixtures" / "rp1-restricted-hosted"
CLI_PATH = REPO_ROOT / "src" / "skilldiff" / "cli.py"
CLAIM_BOUNDARY = (
    "RP1 is simulated restricted-hosted evidence only over an upload-oriented current-case subset. "
    "It is not commercial hosted-runtime behavior, live provider instrumentation, live MCP/plugin behavior, "
    "or public-network evidence. Missing outputs and blocked unsupported surfaces are utility and coverage costs, "
    "not defense-success claims."
)
SUBSET_BOUNDARY = (
    "The RP1 current subset excludes mcp-tool-workflow because RP1 disables MCP/plugin APIs in the profile. "
    "The remaining cases are scaffolded as upload-oriented simulator comparisons only."
)


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


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} must contain a YAML object")
    return data


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


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def adapter_status() -> dict[str, Any]:
    profile = load_yaml(RP1_PROFILE)
    adapter_id = profile["adapter"]["adapter_id"]
    cli_source = CLI_PATH.read_text(encoding="utf-8")
    available = f'if adapter_id == "{adapter_id}"' in cli_source
    return {
        "adapter_id": adapter_id,
        "available": available,
        "reason": None if available else f"tools/skilldiff.py does not yet implement {adapter_id}",
    }


def expected_artifacts() -> dict[str, Any]:
    families = sorted({case["family"] for case in CASES})
    family_artifacts = {
        family: {
            "drift_report": f"results/fixtures/rp1-restricted-hosted/{family}/drift_report.md",
            "comparisons": [
                f"results/fixtures/rp1-restricted-hosted/{family}/{case['case_id']}_rp2_rp3_rp1_comparison.json"
                for case in CASES
                if case["family"] == family
            ],
        }
        for family in families
    }
    return {
        "report_card": "results/fixtures/rp1-restricted-hosted/report_card.json",
        "drift_matrix": "results/fixtures/rp1-restricted-hosted/drift_matrix.md",
        "family_artifacts": family_artifacts,
    }


def write_pending_status() -> Path:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    status_path = OUT_ROOT / "scaffold_status.json"
    payload = {
        "schema_version": "0.1",
        "status": "pending_adapter",
        "runtime_profile": "RP1",
        "adapter_dependency": adapter_status(),
        "case_count": len(CASES),
        "families": sorted({case["family"] for case in CASES}),
        "subset_boundary": SUBSET_BOUNDARY,
        "claim_boundary": CLAIM_BOUNDARY,
        "expected_artifacts": expected_artifacts(),
        "manifest_ref": display_path(MANIFEST),
        "profile_ref": display_path(RP1_PROFILE),
    }
    status_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return status_path


def write_promoted_status(rows: list[dict[str, Any]]) -> Path:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    aggregate = {
        "case_count": len(rows),
        "families": sorted({row["family"] for row in rows}),
        "trace_valid_cases": sum(1 for row in rows if row["summary"]["trace_valid"] is True),
        "simulated_completed_cases": sum(
            1 for row in rows if row["adapter_outcome"] == "simulated_completed" and row["exit_code"] == 0
        ),
        "missing_expected_outputs": sum(row["summary"]["missing_expected_outputs"] for row in rows),
        "realized_contract_violations": sum(row["summary"]["realized_contract_violations"] for row in rows),
        "canary_observations": sum(row["summary"]["canary_observation_count"] for row in rows),
    }
    status_path = OUT_ROOT / "scaffold_status.json"
    payload = {
        "schema_version": "0.1",
        "status": "promoted_deterministic_simulator",
        "runtime_profile": "RP1",
        "adapter_dependency": adapter_status(),
        "aggregate": aggregate,
        "case_count": len(CASES),
        "families": sorted({case["family"] for case in CASES}),
        "subset_boundary": SUBSET_BOUNDARY,
        "claim_boundary": CLAIM_BOUNDARY,
        "expected_artifacts": expected_artifacts(),
        "manifest_ref": display_path(MANIFEST),
        "profile_ref": display_path(RP1_PROFILE),
    }
    status_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return status_path


def annotate_rp1_findings(path: Path) -> None:
    findings = json.loads(path.read_text(encoding="utf-8"))
    findings["adapter_id"] = "restricted_hosted_sim"
    findings["comparison_role"] = "simulated_restricted_hosted"
    findings["comparison_boundary"] = CLAIM_BOUNDARY
    findings["evidence_scope"] = "controlled_semantic_fixture"
    findings["adapter_dependency"] = adapter_status()
    path.write_text(json.dumps(findings, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def compare_case(case: dict[str, Any], rp1_findings: Path) -> None:
    family_dir = OUT_ROOT / case["family"]
    baseline_dir = REPO_ROOT / "results" / "mvp" / case["family"]
    case_id = case["case_id"]
    rp2 = baseline_dir / f"{case_id}_contract_findings.json"
    rp3 = baseline_dir / f"{case_id}_rp3_contract_findings.json"
    out_prefix = family_dir / f"{case_id}_rp2_rp3_rp1_comparison"
    run_text(
        [
            PYTHON,
            "tools/compare_contract_runs.py",
            str(rp2),
            str(rp3),
            str(rp1_findings),
            "--out-json",
            str(out_prefix.with_suffix(".json")),
            "--out-md",
            str(out_prefix.with_suffix(".md")),
        ]
    )


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
            str(RP1_PROFILE),
            "--contract",
            str(contract),
            "--workspace",
            str(workspace),
            "--workspace-seed-id",
            f"{family}-{case_id}-rp1-restricted-hosted",
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
    rp1_findings = family_dir / f"{case_id}_rp1_contract_findings.json"
    run_text(
        [
            PYTHON,
            "tools/check_contract.py",
            "--contract",
            str(contract),
            "--trace",
            result["trace_path"],
            "--out-json",
            str(rp1_findings),
            "--out-md",
            str(family_dir / f"{case_id}_rp1_contract_report.md"),
        ]
    )
    annotate_rp1_findings(rp1_findings)
    compare_case(case, rp1_findings)
    findings = json.loads(rp1_findings.read_text(encoding="utf-8"))
    return {
        "adapter_outcome": result["adapter_outcome"],
        "case_id": case_id,
        "command": case["command"],
        "contract": case["contract"],
        "exit_code": result["exit_code"],
        "family": family,
        "findings_path": display_path(rp1_findings),
        "runtime_profile": findings["runtime_profile"],
        "summary": findings["summary"],
        "trace_path": display_path(Path(result["trace_path"])),
        "variant_id": case["variant_id"],
    }


def write_reports(rows: list[dict[str, Any]]) -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    aggregate = {
        "case_count": len(rows),
        "families": sorted({row["family"] for row in rows}),
        "rp1_realized_contract_violations": sum(row["summary"]["realized_contract_violations"] for row in rows),
        "rp1_attempted_overreach": sum(row["summary"]["attempted_overreach"] for row in rows),
        "rp1_missing_expected_outputs": sum(row["summary"]["missing_expected_outputs"] for row in rows),
        "rp1_canary_observations": sum(row["summary"]["canary_observation_count"] for row in rows),
        "rp1_completed_cases": sum(
            1 for row in rows if row["adapter_outcome"] == "simulated_completed" and row["exit_code"] == 0
        ),
    }
    report_card = {
        "schema_version": "0.2",
        "boundary": CLAIM_BOUNDARY,
        "subset_boundary": SUBSET_BOUNDARY,
        "adapter_dependency": adapter_status(),
        "aggregate": aggregate,
        "cases": rows,
    }
    (OUT_ROOT / "report_card.json").write_text(json.dumps(report_card, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# RP1 Restricted-Hosted Current-Subset Report Card",
        "",
        "RP1 is evaluated only as a deterministic restricted-hosted simulator over the upload-oriented current-case subset.",
        "It is excluded from RP2/RP3 MVP aggregate counts and is not commercial hosted-runtime behavior.",
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
            f"- Realized contract violations: `{aggregate['rp1_realized_contract_violations']}`",
            f"- Attempted overreach: `{aggregate['rp1_attempted_overreach']}`",
            f"- Missing expected outputs: `{aggregate['rp1_missing_expected_outputs']}`",
            f"- Canary observations: `{aggregate['rp1_canary_observations']}`",
            "",
            "## Boundary",
            "",
            CLAIM_BOUNDARY,
            "",
            SUBSET_BOUNDARY,
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
    write_promoted_status(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the RP1 restricted-hosted current-subset scaffold")
    parser.add_argument(
        "--require-adapter",
        action="store_true",
        help="Fail instead of writing scaffold_status.json when restricted_hosted_sim is unavailable.",
    )
    args = parser.parse_args(argv)

    status = adapter_status()
    if not status["available"]:
        status_path = write_pending_status()
        if args.require_adapter:
            print(status["reason"], file=sys.stderr)
            return 1
        print(status_path)
        return 0

    rows = [run_case(case) for case in CASES]
    write_reports(rows)
    print(OUT_ROOT / "report_card.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
