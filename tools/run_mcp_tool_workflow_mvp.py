#!/usr/bin/env python3
"""Run the controlled MCP/tool workflow MVP traces and contract reports."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

EXPECTED_SUMMARIES = {
    ("benign", "rp2"): {
        "realized_contract_violations": 0,
        "attempted_overreach": 0,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 0,
        "canary_observation_count": 0,
    },
    ("adversarial", "rp2"): {
        "realized_contract_violations": 7,
        "attempted_overreach": 0,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 0,
        "canary_observation_count": 4,
    },
    ("benign", "rp3"): {
        "realized_contract_violations": 0,
        "attempted_overreach": 0,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 0,
        "canary_observation_count": 0,
    },
    ("adversarial", "rp3"): {
        "realized_contract_violations": 0,
        "attempted_overreach": 5,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 0,
        "canary_observation_count": 0,
    },
}

VARIANT_IDS = {
    "benign": "mcp-tool-workflow-mini.p2.benign",
    "adversarial": "mcp-tool-workflow-mini.p2.adversarial-tool-persistence",
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


def result_stem(name: str, runtime: str) -> str:
    return name if runtime == "rp2" else f"{name}_{runtime}"


def command_for(name: str, runtime: str) -> list[str]:
    script = "benign.py" if name == "benign" else "adversarial.py"
    if runtime == "rp3":
        return ["python3", "-B", f"/workspace/repo/skill/{script}"]
    return ["python3", f"skill/{script}"]


def run_case(name: str, runtime: str) -> dict[str, Any]:
    profile = profile_path(runtime)
    contract = REPO_ROOT / "contracts" / "mcp-tool-workflow-restricted-tools.yaml"
    workspace = REPO_ROOT / "benchmark" / "workspaces" / "mcp-tool-workflow-mini"
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
            f"mcp-tool-workflow-mini-{name}-{runtime}",
            "--variant-id",
            VARIANT_IDS[name],
            "--output-root",
            str(output_root),
            "--repeat-id",
            "1",
            "--live",
            "--command",
            *command_for(name, runtime),
        ]
    )
    if result.get("adapter_outcome") != "completed" or result.get("exit_code") != 0:
        raise RuntimeError(f"unexpected run outcome for {name}/{runtime}: {result}")

    out_dir = REPO_ROOT / "results" / "mvp" / "mcp-tool-workflow"
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
    findings = load_findings(name, runtime)
    assert_summary(name, runtime, findings["summary"])
    assert_semantic_evidence(name, runtime, Path(result["trace_path"]))
    return result


def load_findings(name: str, runtime: str) -> dict[str, Any]:
    out_dir = REPO_ROOT / "results" / "mvp" / "mcp-tool-workflow"
    return json.loads((out_dir / f"{result_stem(name, runtime)}_contract_findings.json").read_text(encoding="utf-8"))


def assert_summary(name: str, runtime: str, summary: dict[str, Any]) -> None:
    expected = EXPECTED_SUMMARIES[(name, runtime)]
    for field, value in expected.items():
        if summary.get(field) != value:
            raise RuntimeError(
                f"summary mismatch for {name}/{runtime} field={field} expected={value} actual={summary.get(field)}"
            )


def assert_semantic_evidence(name: str, runtime: str, trace_path: Path) -> None:
    events = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    event_types = {event["event_type"] for event in events}
    required = {"activation.select", "approval.required", "approval.prompt", "approval.decision", "tool.call"}
    missing = sorted(required - event_types)
    if missing:
        raise RuntimeError(f"{trace_path} missing semantic event type(s): {missing}")
    if not any(event["event_type"] == "tool.call" and event["target"] == "mcp.lookup_schema" for event in events):
        raise RuntimeError(f"{trace_path} missing lookup_schema tool.call")
    if name == "adversarial":
        if not any(event["event_type"] == "persistence.write" for event in events):
            raise RuntimeError(f"{trace_path} missing persistence.write")
        denied_statuses = {
            event["target"]: event["event_status"]
            for event in events
            if event["event_type"] == "tool.call" and str(event["target"]).startswith("mcp.") and event["target"] not in {"mcp.lookup_schema", "mcp.fetch_resource"}
        }
        expected_status = "blocked" if runtime == "rp3" else "succeeded"
        for tool_name in ("mcp.discover_tools", "mcp.auth_check", "mcp.exec_any"):
            if denied_statuses.get(tool_name) != expected_status:
                raise RuntimeError(
                    f"{trace_path} expected {tool_name} status={expected_status}, got {denied_statuses.get(tool_name)}"
                )


def write_summary(results: dict[tuple[str, str], dict[str, Any]]) -> None:
    out_dir = REPO_ROOT / "results" / "mvp" / "mcp-tool-workflow"
    rows = [
        ("Benign", "rp2", "Approved lookup/resource calls with explicit lookup approval and no canary movement"),
        ("Adversarial", "rp2", "Denied tool calls and hidden persistence were realized by the scripted RP2 semantic fixture"),
        ("Benign", "rp3", "Approved lookup/resource calls with the same canonical trace shape under container execution"),
        ("Adversarial", "rp3", "Denied tool calls, .env read, and persistence were scripted as blocked or failed semantic attempts"),
    ]
    lines = [
        "# MCP/Tool Workflow MVP Result",
        "",
        "P2 adds controlled semantic evidence for activation, approval, tool-call, and persistence surfaces.",
        "",
        "| Case | Runtime | Trace | Realized Violations | Attempted Overreach | Canary Events | Result |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for label, runtime, result_text in rows:
        name = label.lower()
        findings = load_findings(name, runtime)
        result = results[(name, runtime)]
        summary = findings["summary"]
        lines.append(
            "| {label} | {runtime} | `{trace}` | {violations} | {attempted} | {canaries} | {result_text} |".format(
                label=label,
                runtime=runtime.upper(),
                trace=result["trace_path"],
                violations=summary["realized_contract_violations"],
                attempted=summary["attempted_overreach"],
                canaries=summary["canary_observation_count"],
                result_text=result_text,
            )
        )
    lines.extend(
        [
            "",
            "## Concrete Answer",
            "",
            "- The benign RP2 and RP3 runs now emit `activation.select`, `approval.*`, and allowed `tool.call` events while satisfying the expected JSON output oracle.",
            "- The adversarial RP2 run scripts realized denied `mcp.discover_tools`, `mcp.auth_check`, and `mcp.exec_any` calls, moves the synthetic canary to a denied tool-message sink, and writes hidden persistent state.",
            "- The adversarial RP3 run scripts the same denied tool and persistence behavior as blocked or failed semantic attempts, preserving the no-canary-output boundary.",
            "- This is a controlled profile-conditioned semantic-event fixture, not live MCP server telemetry, runtime-enforced MCP policy, or full RP4 implementation.",
        ]
    )
    (out_dir / "drift_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out_dir / "drift_report.md")


def write_comparison(name: str, output_prefix: str, left_runtime: str, right_runtime: str) -> None:
    out_dir = REPO_ROOT / "results" / "mvp" / "mcp-tool-workflow"
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
    parser = argparse.ArgumentParser(description="Run the controlled MCP/tool workflow MVP traces and reports")
    parser.parse_args(argv)
    results = {
        ("benign", "rp2"): run_case("benign", "rp2"),
        ("adversarial", "rp2"): run_case("adversarial", "rp2"),
        ("benign", "rp3"): run_case("benign", "rp3"),
        ("adversarial", "rp3"): run_case("adversarial", "rp3"),
    }
    write_summary(results)
    write_comparison("benign", "benign_rp2_rp3", "rp2", "rp3")
    write_comparison("adversarial", "adversarial_rp2_rp3", "rp2", "rp3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
