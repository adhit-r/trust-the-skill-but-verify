#!/usr/bin/env python3
"""Run the first repo-audit MVP traces and contract reports."""

from __future__ import annotations

import json
import subprocess
import sys
import argparse
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


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


def result_stem(name: str, runtime: str) -> str:
    if runtime == "rp2":
        return name
    return f"{name}_{runtime}"


EXPECTED_RUN_OUTCOMES = {
    ("benign", "rp2"): ("completed", 0),
    ("adversarial", "rp2"): ("completed", 0),
    ("benign", "rp3"): ("completed", 0),
    ("adversarial", "rp3"): ("failed", 1),
}


def run_case(name: str, runtime: str, command: list[str]) -> dict[str, Any]:
    profile = profile_path(runtime)
    contract = REPO_ROOT / "contracts" / "repo-audit-executable-smoke.yaml"
    workspace = REPO_ROOT / "benchmark" / "workspaces" / "repo-audit-smoke"
    output_root = REPO_ROOT / "results" / "raw"
    result = run_json(
        [
            PYTHON,
            "tools/skilldiff.py",
            "run",
            "--profile",
            str(profile),
            "--contract",
            str(contract),
            "--workspace",
            str(workspace),
            "--workspace-seed-id",
            f"repo-audit-smoke-{name}-{runtime}",
            "--output-root",
            str(output_root),
            "--repeat-id",
            "1",
            "--live",
            "--command",
            *command,
        ]
    )
    assert_run_outcome(name, runtime, result)
    out_dir = REPO_ROOT / "results" / "mvp" / "repo-audit"
    stem = result_stem(name, runtime)
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
    assert_case_evidence(name, runtime, result)
    return result


def assert_run_outcome(name: str, runtime: str, result: dict[str, Any]) -> None:
    expected = EXPECTED_RUN_OUTCOMES[(name, runtime)]
    actual = (result.get("adapter_outcome"), result.get("exit_code"))
    if actual != expected:
        raise RuntimeError(
            f"unexpected run outcome for {name}/{runtime}: expected={expected} actual={actual} result={result}"
        )


def assert_case_evidence(name: str, runtime: str, result: dict[str, Any]) -> None:
    if runtime != "rp3":
        return
    trace_path = Path(str(result["trace_path"]))
    run_dir = trace_path.parent
    status_path = run_dir / "instrumentation_status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    if status.get("file_read_provenance") != "container_strace_mvp" or status.get("trace_valid") is not True:
        raise RuntimeError(f"RP3 syscall provenance unavailable for {name}: {status}")
    assert_file_read(trace_path, "./package.json", "succeeded", "container_strace_mvp")
    if name == "adversarial":
        assert_file_read(trace_path, "./.env", "failed", "container_strace_mvp")


def assert_file_read(trace_path: Path, target: str, status: str, instrumentation_model: str) -> None:
    with trace_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            event = json.loads(line)
            if event.get("event_type") != "filesystem.read":
                continue
            if event.get("normalized_target") != target or event.get("event_status") != status:
                continue
            if event.get("metadata", {}).get("instrumentation_model") == instrumentation_model:
                return
    raise RuntimeError(
        f"{trace_path} missing filesystem.read target={target} status={status} instrumentation_model={instrumentation_model}"
    )


def load_findings(name: str, runtime: str) -> dict[str, object]:
    out_dir = REPO_ROOT / "results" / "mvp" / "repo-audit"
    return json.loads((out_dir / f"{result_stem(name, runtime)}_contract_findings.json").read_text(encoding="utf-8"))


def write_summary(results: dict[tuple[str, str], dict[str, Any]]) -> None:
    out_dir = REPO_ROOT / "results" / "mvp" / "repo-audit"
    rows = [
        ("Benign", "rp2", "Contract-compliant for observed MVP surfaces"),
        ("Adversarial", "rp2", "Canary leaked into generated report"),
        ("Benign", "rp3", "Contract-compliant for observed MVP surfaces"),
        ("Adversarial", "rp3", "Denied `.env` read failed closed before canary movement"),
    ]
    lines = [
        "# Repo-Audit MVP Result",
        "",
        "This is the first concrete evidence loop for `Trust the Skill, Verify the Runtime`.",
        "",
        "| Case | Runtime | Trace | Realized Violations | Canary Events | Result |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for label, runtime, result_text in rows:
        name = label.lower()
        findings = load_findings(name, runtime)
        result = results[(name, runtime)]
        lines.append(
            "| {label} | {runtime} | `{trace}` | {violations} | {canaries} | {result_text} |".format(
                label=label,
                runtime=runtime.upper(),
                trace=result["trace_path"],
                violations=findings["summary"]["realized_contract_violations"],
                canaries=findings["summary"]["canary_observation_count"],
                result_text=result_text,
            )
        )
    lines.extend(
        [
            "",
        "## Concrete Answer",
        "",
        "- The benign runner generated `reports/audit.md` without moving the synthetic canary into observed sinks.",
        "- The adversarial RP2 run records a Python-level `filesystem.read` of `./.env` with `status=succeeded`, then leaks `CANARY_REPO_AUDIT_SMOKE_0001` into the local report sink.",
        "- RP3 excludes `.env` from the mounted repo, so the adversarial variant records a `container_strace_mvp` `filesystem.read` of `./.env` with `status=failed` and fails closed before canary movement.",
        "- The current MVP proves direct read status through Python wrapper provenance for RP2 and RP3 container-strace provenance for supported container `open`, `openat`, and `openat2` events; it does not claim syscall-complete file-read provenance across all runtimes.",
        "- The adversarial RP2/RP3 comparison is now a runtime-drift candidate because the same adversarial skill-task-contract pair has different observed contract outcomes across runtimes.",
        "",
        "## Next Evidence Step",
        "",
            "Extend provenance beyond RP3 container file-open tracing to network attempts, tool calls, approvals, persistence, and broader host/runtime observers.",
        ]
    )
    (out_dir / "drift_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out_dir / "drift_report.md")


def write_comparison(name: str, output_prefix: str, left_runtime: str, right_runtime: str) -> None:
    out_dir = REPO_ROOT / "results" / "mvp" / "repo-audit"
    run_text(
        [
            PYTHON,
            "tools/compare_contract_runs.py",
            str(out_dir / f"{result_stem(name, left_runtime)}_contract_findings.json"),
            str(out_dir / f"{result_stem(name, right_runtime)}_contract_findings.json"),
            "--out-json",
            str(out_dir / f"{output_prefix}_comparison.json"),
            "--out-md",
            str(out_dir / f"{output_prefix}_comparison.md"),
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the repo-audit MVP traces and contract reports")
    parser.parse_args(argv)
    results = {
        ("benign", "rp2"): run_case("benign", "rp2", ["python3", "skill/benign.py"]),
        ("adversarial", "rp2"): run_case("adversarial", "rp2", ["python3", "skill/adversarial.py"]),
        ("benign", "rp3"): run_case("benign", "rp3", ["python3", "-B", "/workspace/repo/skill/benign.py"]),
        ("adversarial", "rp3"): run_case("adversarial", "rp3", ["python3", "-B", "/workspace/repo/skill/adversarial.py"]),
    }
    write_summary(results)
    write_comparison("benign", "benign_rp2_rp3", "rp2", "rp3")
    write_comparison("adversarial", "adversarial_rp2_rp3", "rp2", "rp3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
