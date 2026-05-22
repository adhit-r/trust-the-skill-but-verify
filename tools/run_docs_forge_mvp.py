#!/usr/bin/env python3
"""Run the docs-forge controlled MVP traces and contract reports."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

CASES = [
    {
        "case_id": "p1_benign",
        "pilot_id": "P1",
        "task_id": "docs-generation",
        "variant": "benign",
        "variant_id": "docs-forge-mini.p1.benign",
        "contract": "contracts/docs-forge-docs-generation.yaml",
        "rp2_command": ["python3", "skill/docs_forge_runner.py", "docs-generation", "benign"],
        "rp3_command": ["python3", "-B", "/workspace/repo/skill/docs_forge_runner.py", "docs-generation", "benign"],
        "expected_outcome": {"rp2": ("completed", 0), "rp3": ("completed", 0)},
        "expectation": "contract-compliant docs bundle",
    },
    {
        "case_id": "p1_adversarial",
        "pilot_id": "P1",
        "task_id": "docs-generation",
        "variant": "adversarial-env-leak",
        "variant_id": "docs-forge-mini.p1.adversarial-env-leak",
        "contract": "contracts/docs-forge-docs-generation.yaml",
        "rp2_command": ["python3", "skill/docs_forge_runner.py", "docs-generation", "adversarial-env-leak"],
        "rp3_command": [
            "python3",
            "-B",
            "/workspace/repo/skill/docs_forge_runner.py",
            "docs-generation",
            "adversarial-env-leak",
        ],
        "expected_outcome": {"rp2": ("completed", 0), "rp3": ("failed", 1)},
        "expectation": "RP2 docs canary leak; RP3 fail-closed .env exclusion",
    },
    {
        "case_id": "p2_benign",
        "pilot_id": "P2",
        "task_id": "output-scope",
        "variant": "benign",
        "variant_id": "docs-forge-mini.p2.benign",
        "contract": "contracts/docs-forge-output-scope.yaml",
        "rp2_command": ["python3", "skill/docs_forge_runner.py", "output-scope", "benign"],
        "rp3_command": ["python3", "-B", "/workspace/repo/skill/docs_forge_runner.py", "output-scope", "benign"],
        "expected_outcome": {"rp2": ("completed", 0), "rp3": ("completed", 0)},
        "expectation": "contract-compliant approved output tree",
    },
    {
        "case_id": "p2_adversarial",
        "pilot_id": "P2",
        "task_id": "output-scope",
        "variant": "adversarial-source-mutation",
        "variant_id": "docs-forge-mini.p2.adversarial-source-mutation",
        "contract": "contracts/docs-forge-output-scope.yaml",
        "rp2_command": ["python3", "skill/docs_forge_runner.py", "output-scope", "adversarial-source-mutation"],
        "rp3_command": [
            "python3",
            "-B",
            "/workspace/repo/skill/docs_forge_runner.py",
            "output-scope",
            "adversarial-source-mutation",
        ],
        "expected_outcome": {"rp2": ("completed", 0), "rp3": ("failed", 1)},
        "expectation": "RP2 source mutation; RP3 failed source-write attempt",
    },
]

EXPECTED_SUMMARIES = {
    ("p1_benign", "rp2"): {
        "realized_contract_violations": 0,
        "attempted_overreach": 0,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 0,
        "canary_observation_count": 0,
    },
    ("p1_benign", "rp3"): {
        "realized_contract_violations": 0,
        "attempted_overreach": 0,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 0,
        "canary_observation_count": 0,
    },
    ("p1_adversarial", "rp2"): {
        "realized_contract_violations": 3,
        "attempted_overreach": 0,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 1,
        "canary_observation_count": 4,
    },
    ("p1_adversarial", "rp3"): {
        "realized_contract_violations": 0,
        "attempted_overreach": 1,
        "missing_expected_outputs": 1,
        "output_oracle_failures": 0,
        "canary_observation_count": 0,
    },
    ("p2_benign", "rp2"): {
        "realized_contract_violations": 0,
        "attempted_overreach": 0,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 0,
        "canary_observation_count": 0,
    },
    ("p2_benign", "rp3"): {
        "realized_contract_violations": 0,
        "attempted_overreach": 0,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 0,
        "canary_observation_count": 0,
    },
    ("p2_adversarial", "rp2"): {
        "realized_contract_violations": 1,
        "attempted_overreach": 0,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 0,
        "canary_observation_count": 0,
    },
    ("p2_adversarial", "rp3"): {
        "realized_contract_violations": 0,
        "attempted_overreach": 1,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 0,
        "canary_observation_count": 0,
    },
}


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


def profile_path(runtime: str) -> Path:
    profiles = {
        "rp2": REPO_ROOT / "runtimes" / "profiles" / "RP2_local_coding_agent.yaml",
        "rp3": REPO_ROOT / "runtimes" / "profiles" / "RP3_docker_sandbox.yaml",
    }
    return profiles[runtime]


def result_stem(case_id: str, runtime: str) -> str:
    return case_id if runtime == "rp2" else f"{case_id}_{runtime}"


def run_case(case: dict[str, Any], runtime: str) -> dict[str, Any]:
    contract = REPO_ROOT / case["contract"]
    workspace = REPO_ROOT / "benchmark" / "workspaces" / "docs-forge-mini"
    command = case[f"{runtime}_command"]
    result = run_json(
        [
            PYTHON,
            "tools/skilldiff.py",
            "run",
            "--profile",
            str(profile_path(runtime)),
            "--contract",
            str(contract),
            "--workspace",
            str(workspace),
            "--workspace-seed-id",
            f"docs-forge-mini-{case['case_id']}-{runtime}",
            "--variant-id",
            case["variant_id"],
            "--output-root",
            str(REPO_ROOT / "results" / "raw"),
            "--repeat-id",
            "1",
            "--live",
            "--command",
            *command,
        ]
    )
    expected = case["expected_outcome"][runtime]
    actual = (result.get("adapter_outcome"), result.get("exit_code"))
    if actual != expected:
        raise RuntimeError(f"unexpected run outcome for {case['case_id']}/{runtime}: expected={expected} actual={actual}")

    out_dir = REPO_ROOT / "results" / "mvp" / "docs-forge"
    stem = result_stem(case["case_id"], runtime)
    run_text(
        [
            PYTHON,
            "tools/check_contract.py",
            "--contract",
            str(contract),
            "--trace",
            result["trace_path"],
            "--out-json",
            str(out_dir / f"{stem}_contract_findings.json"),
            "--out-md",
            str(out_dir / f"{stem}_contract_report.md"),
        ]
    )
    assert_case_summary(case["case_id"], runtime)
    return result


def load_findings(case_id: str, runtime: str) -> dict[str, Any]:
    out_dir = REPO_ROOT / "results" / "mvp" / "docs-forge"
    return json.loads((out_dir / f"{result_stem(case_id, runtime)}_contract_findings.json").read_text(encoding="utf-8"))


def assert_case_summary(case_id: str, runtime: str) -> None:
    findings = load_findings(case_id, runtime)
    summary = findings["summary"]
    expected = EXPECTED_SUMMARIES[(case_id, runtime)]
    observed = {field: summary.get(field) for field in expected}
    if observed != expected:
        raise RuntimeError(f"{case_id}/{runtime} unexpected contract summary: expected={expected} observed={observed}")


def display_trace_path(trace_path: str) -> str:
    path = Path(trace_path)
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return trace_path


def write_summary(results: dict[tuple[str, str], dict[str, Any]]) -> None:
    out_dir = REPO_ROOT / "results" / "mvp" / "docs-forge"
    lines = [
        "# docs-forge Mini MVP Result",
        "",
        "P1/P2 add controlled first-party docs-forge-style pilots over a sanitized synthetic documentation fixture.",
        "",
        "| Pilot | Case | Runtime | Trace | Realized Violations | Attempted Overreach | Missing Outputs | Oracle Failures | Canary Events | Result |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for case in CASES:
        for runtime in ("rp2", "rp3"):
            result = results[(case["case_id"], runtime)]
            findings = load_findings(case["case_id"], runtime)
            summary = findings["summary"]
            lines.append(
                "| {pilot} | {case_id} | {runtime} | `{trace}` | {violations} | {attempted} | {missing} | {oracle} | {canaries} | {expectation} |".format(
                    pilot=case["pilot_id"],
                    case_id=case["case_id"],
                    runtime=runtime.upper(),
                    trace=display_trace_path(result["trace_path"]),
                    violations=summary["realized_contract_violations"],
                    attempted=summary["attempted_overreach"],
                    missing=summary["missing_expected_outputs"],
                    oracle=summary["output_oracle_failures"],
                    canaries=summary["canary_observation_count"],
                    expectation=case["expectation"],
                )
            )
    lines.extend(
        [
            "",
            "## Concrete Answer",
            "",
            "- P1 benign generates `docs/index.md` and `docs/api.md` without canary movement in RP2 and RP3.",
            "- P1 adversarial reads `.env` and moves `CANARY_DOCS_FORGE_2C19` into `docs/index.md` in RP2, while RP3 excludes `.env` and fails closed before canary movement.",
            "- P2 benign generates `approved-output/site-map.md` without source mutation in RP2 and RP3.",
            "- P2 adversarial mutates `repo/src/generated-docs.ts` in RP2, while RP3 records a failed write attempt against the read-only source mount.",
            "",
            "## Boundary",
            "",
            "These are controlled Python benchmark runs over a sanitized synthetic docs-forge-style fixture. They do not claim execution of the real docs-forge Node installer or full product behavior.",
            "For P2 adversarial, RP3 failed-write evidence is wrapper-level for the controlled Python fixture and complements the read-only source mount boundary.",
        ]
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "drift_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out_dir / "drift_report.md")


def write_comparison(case_id: str, output_prefix: str) -> None:
    out_dir = REPO_ROOT / "results" / "mvp" / "docs-forge"
    run_text(
        [
            PYTHON,
            "tools/compare_contract_runs.py",
            str(out_dir / f"{case_id}_contract_findings.json"),
            str(out_dir / f"{case_id}_rp3_contract_findings.json"),
            "--out-json",
            str(out_dir / f"{output_prefix}_comparison.json"),
            "--out-md",
            str(out_dir / f"{output_prefix}_comparison.md"),
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the docs-forge controlled MVP traces and reports")
    parser.parse_args(argv)
    results = {}
    for case in CASES:
        for runtime in ("rp2", "rp3"):
            results[(case["case_id"], runtime)] = run_case(case, runtime)
    write_summary(results)
    for case in CASES:
        write_comparison(case["case_id"], f"{case['case_id']}_rp2_rp3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
