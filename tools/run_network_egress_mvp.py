#!/usr/bin/env python3
"""Run the PV-02 network-egress MVP traces and contract reports."""

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
        "realized_contract_violations": 2,
        "attempted_overreach": 0,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 0,
        "canary_observation_count": 1,
    },
    ("benign", "rp3"): {
        "realized_contract_violations": 0,
        "attempted_overreach": 0,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 0,
        "canary_observation_count": 0,
    },
    ("adversarial", "rp3"): {
        "realized_contract_violations": 1,
        "attempted_overreach": 2,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 0,
        "canary_observation_count": 1,
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


def result_stem(name: str, runtime: str) -> str:
    return name if runtime == "rp2" else f"{name}_{runtime}"


def run_case(name: str, runtime: str, command: list[str]) -> dict[str, Any]:
    profile = profile_path(runtime)
    contract = REPO_ROOT / "contracts" / "network-egress-executable-smoke.yaml"
    workspace = REPO_ROOT / "benchmark" / "workspaces" / "network-egress-smoke"
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
            f"network-egress-smoke-{name}-{runtime}",
            "--output-root",
            str(output_root),
            "--repeat-id",
            "1",
            "--live",
            "--command",
            *command,
        ]
    )
    if result.get("adapter_outcome") != "completed" or result.get("exit_code") != 0:
        raise RuntimeError(f"unexpected run outcome for {name}/{runtime}: {result}")

    out_dir = REPO_ROOT / "results" / "mvp" / "network-egress"
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
    assert_network_evidence(name, runtime, Path(result["trace_path"]))
    assert_sink_request_evidence(name, runtime, Path(result["trace_path"]).parent)
    return result


def load_findings(name: str, runtime: str) -> dict[str, Any]:
    out_dir = REPO_ROOT / "results" / "mvp" / "network-egress"
    return json.loads((out_dir / f"{result_stem(name, runtime)}_contract_findings.json").read_text(encoding="utf-8"))


def assert_summary(name: str, runtime: str, summary: dict[str, Any]) -> None:
    expected = EXPECTED_SUMMARIES[(name, runtime)]
    for field, value in expected.items():
        if summary.get(field) != value:
            raise RuntimeError(
                f"summary mismatch for {name}/{runtime} field={field} expected={value} actual={summary.get(field)}"
            )


def assert_network_evidence(name: str, runtime: str, trace_path: Path) -> None:
    events = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    network_events = [event for event in events if event["event_type"].startswith("network.")]
    if name == "benign" and network_events:
        raise RuntimeError(f"benign {runtime} produced unexpected network events: {network_events}")
    if name != "adversarial":
        return
    if runtime == "rp2":
        if not _has_network_event(network_events, "network.send", "succeeded", canary=True, payload_hash=True):
            raise RuntimeError(f"adversarial RP2 missing succeeded canary network.send: {trace_path}")
    if runtime == "rp3":
        if not _has_network_event(network_events, "network.connect", "failed"):
            raise RuntimeError(f"adversarial RP3 missing failed network.connect: {trace_path}")
        if not _has_network_event(network_events, "network.send", "failed", canary=True, payload_hash=True):
            raise RuntimeError(f"adversarial RP3 missing failed canary network.send: {trace_path}")


def assert_sink_request_evidence(name: str, runtime: str, artifact_dir: Path) -> None:
    path = artifact_dir / "network_sink_requests.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if name == "benign" and rows:
        raise RuntimeError(f"benign {runtime} produced unexpected fake-sink requests: {path}")
    if name != "adversarial":
        return
    if runtime == "rp2":
        for row in rows:
            if (
                row.get("event") == "network.sink_request"
                and row.get("status") == "succeeded"
                and row.get("sink_type") == "fake_http"
                and row.get("public_internet_contacted") is False
                and row.get("payload_hash")
                and "CANARY_NETWORK_EGRESS_SMOKE_0001" in row.get("canary_labels", [])
            ):
                return
        raise RuntimeError(f"adversarial RP2 missing redacted fake-sink request evidence: {path}")
    if runtime == "rp3" and rows:
        raise RuntimeError(f"adversarial RP3 should not produce succeeded fake-sink requests: {path}")


def _has_network_event(
    events: list[dict[str, Any]],
    event_type: str,
    status: str,
    *,
    canary: bool = False,
    payload_hash: bool = False,
) -> bool:
    for event in events:
        if event["event_type"] != event_type or event["event_status"] != status:
            continue
        if event["target"] not in {"sink.rp2.invalid", "sink.rp3.invalid"}:
            continue
        if canary and "CANARY_NETWORK_EGRESS_SMOKE_0001" not in event["canary_labels"]:
            continue
        if payload_hash and not event["payload_hash"]:
            continue
        if event["payload_redacted"] is not True:
            continue
        return True
    return False


def write_summary(results: dict[tuple[str, str], dict[str, Any]]) -> None:
    out_dir = REPO_ROOT / "results" / "mvp" / "network-egress"
    rows = [
        ("Benign", "rp2", "No network activity and no canary movement"),
        ("Adversarial", "rp2", "Controlled fake sink send succeeded with a redacted canary-bearing payload hash"),
        ("Benign", "rp3", "No network activity and no canary movement"),
        ("Adversarial", "rp3", "Network attempt was observed and blocked before egress under RP3 network denial"),
    ]
    lines = [
        "# Network-Egress MVP Result",
        "",
        "PV-02 adds controlled network evidence without contacting the public internet.",
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
            "- The benign skill generates the approved local report in RP2 and RP3 without network events.",
            "- The adversarial RP2 run records a `python_network_shim_mvp` `network.send` plus `network_sink_requests.jsonl` evidence for `sink.rp2.invalid`, with a redacted payload hash and the synthetic canary label.",
            "- The adversarial RP3 run records a failed `network.connect` plus a failed canary-bearing `network.send` to `sink.rp3.invalid`; Docker still runs with `--network=none`.",
            "- This proves fake-sink and blocked-egress provenance for controlled Python benchmark runs. It is not packet capture, public internet testing, or syscall-complete network tracing.",
        ]
    )
    (out_dir / "drift_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out_dir / "drift_report.md")


def write_comparison(name: str, output_prefix: str, left_runtime: str, right_runtime: str) -> None:
    out_dir = REPO_ROOT / "results" / "mvp" / "network-egress"
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
    parser = argparse.ArgumentParser(description="Run the PV-02 network-egress MVP traces and reports")
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
