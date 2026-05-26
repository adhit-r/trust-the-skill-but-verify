#!/usr/bin/env python3
"""Run the RP5 plugin-style fixture report card."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
RP5_PROFILE = REPO_ROOT / "runtimes" / "profiles" / "RP5_plugin_style.yaml"
OUT_ROOT = REPO_ROOT / "results" / "fixtures" / "rp5-plugin-style"
CLAIM_BOUNDARY = (
    "RP5 is fixture-backed plugin-style evidence over local synthetic plugin metadata, bundled resources, "
    "fixture host APIs, scoped run storage, and activation negative controls. It is not commercial plugin-store "
    "behavior, live host API behavior, external MCP/server behavior, public-network evidence, or a defense-success claim."
)


CASES = [
    {
        "case_id": "install_activation",
        "contract": "contracts/rp5-plugin-install-activation.yaml",
        "workspace": "benchmark/workspaces/rp5-plugin-style-mini",
        "variant_id": "rp5-plugin-style.benign.install_activation",
        "command": ["sh", "plugin/install.sh", "--fixture"],
    },
    {
        "case_id": "update_metadata",
        "contract": "contracts/rp5-plugin-update-metadata.yaml",
        "workspace": "benchmark/workspaces/rp5-plugin-style-mini",
        "variant_id": "rp5-plugin-style.benign.update_metadata",
        "command": [],
    },
    {
        "case_id": "negative_control",
        "contract": "contracts/rp5-plugin-negative-control.yaml",
        "workspace": "benchmark/workspaces/rp5-plugin-style-mini",
        "variant_id": "rp5-plugin-style.negative-control",
        "command": [],
    },
]


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


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    case_id = case["case_id"]
    contract = REPO_ROOT / case["contract"]
    workspace = REPO_ROOT / case["workspace"]
    args = [
        PYTHON,
        "tools/skilldiff.py",
        "run",
        "--profile",
        str(RP5_PROFILE),
        "--contract",
        str(contract),
        "--workspace",
        str(workspace),
        "--workspace-seed-id",
        f"plugin-style-{case_id}-rp5-plugin-style",
        "--variant-id",
        case["variant_id"],
        "--output-root",
        str(OUT_ROOT / "_runs"),
        "--repeat-id",
        "1",
        "--live",
    ]
    if case["command"]:
        args.extend(["--command", *case["command"]])
    result = run_json(args)

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    findings_path = OUT_ROOT / f"{case_id}_rp5_contract_findings.json"
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
            str(OUT_ROOT / f"{case_id}_rp5_contract_report.md"),
        ]
    )
    annotate_rp5_findings(findings_path)
    findings = json.loads(findings_path.read_text(encoding="utf-8"))
    return {
        "adapter_outcome": result["adapter_outcome"],
        "case_id": case_id,
        "command": case["command"],
        "contract": case["contract"],
        "exit_code": result["exit_code"],
        "family": "plugin-style",
        "findings_path": display_path(findings_path),
        "runtime_profile": findings["runtime_profile"],
        "summary": findings["summary"],
        "trace_path": display_path(Path(result["trace_path"])),
        "variant_id": case["variant_id"],
    }


def annotate_rp5_findings(path: Path) -> None:
    findings = json.loads(path.read_text(encoding="utf-8"))
    findings["adapter_id"] = "plugin_fixture_adapter"
    findings["comparison_role"] = "plugin_fixture_report_card"
    findings["comparison_boundary"] = CLAIM_BOUNDARY
    findings["evidence_scope"] = "controlled_plugin_fixture"
    path.write_text(json.dumps(findings, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_reports(rows: list[dict[str, Any]]) -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    aggregate = {
        "case_count": len(rows),
        "families": sorted({row["family"] for row in rows}),
        "rp5_activation_negative_controls": sum(1 for row in rows if row["case_id"] == "negative_control"),
        "rp5_attempted_overreach": sum(row["summary"]["attempted_overreach"] for row in rows),
        "rp5_canary_observations": sum(row["summary"]["canary_observation_count"] for row in rows),
        "rp5_completed_cases": sum(
            1 for row in rows if row["adapter_outcome"] == "fixture_completed" and row["exit_code"] == 0
        ),
        "rp5_missing_expected_outputs": sum(row["summary"]["missing_expected_outputs"] for row in rows),
        "rp5_realized_contract_violations": sum(row["summary"]["realized_contract_violations"] for row in rows),
    }
    report_card = {
        "schema_version": "0.1",
        "boundary": CLAIM_BOUNDARY,
        "aggregate": aggregate,
        "cases": rows,
    }
    (OUT_ROOT / "report_card.json").write_text(json.dumps(report_card, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# RP5 Plugin-Style Fixture Report Card",
        "",
        "RP5 is evaluated as a bounded local plugin-style fixture. It is fixture-backed and not commercial plugin-store behavior.",
        "",
        "| Case | Outcome | Realized | Attempted | Missing Outputs | Oracle Failures | Canary Events | Trace |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        summary = row["summary"]
        lines.append(
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
    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            f"- Cases: `{aggregate['case_count']}`",
            f"- Activation negative controls: `{aggregate['rp5_activation_negative_controls']}`",
            f"- Realized contract violations: `{aggregate['rp5_realized_contract_violations']}`",
            f"- Attempted overreach: `{aggregate['rp5_attempted_overreach']}`",
            f"- Missing expected outputs: `{aggregate['rp5_missing_expected_outputs']}`",
            f"- Canary observations: `{aggregate['rp5_canary_observations']}`",
            "",
            "## Boundary",
            "",
            CLAIM_BOUNDARY,
        ]
    )
    (OUT_ROOT / "drift_matrix.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the RP5 plugin-style fixture report card")
    parser.parse_args(argv)
    rows = [run_case(case) for case in CASES]
    write_reports(rows)
    print(OUT_ROOT / "report_card.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
