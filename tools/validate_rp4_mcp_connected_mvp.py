#!/usr/bin/env python3
"""Validate bounded RP4 MCP-connected fixture artifacts."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TRACE_PATHS = {
    "benign": REPO_ROOT / "results" / "raw" / "rp4-mcp-connected-benign" / "trace.jsonl",
    "adversarial": REPO_ROOT / "results" / "raw" / "rp4-mcp-connected-adversarial" / "trace.jsonl",
}
FINDINGS_PATHS = {
    "benign": REPO_ROOT / "results" / "fixtures" / "rp4-mcp-connected" / "benign_contract_findings.json",
    "adversarial": REPO_ROOT / "results" / "fixtures" / "rp4-mcp-connected" / "adversarial_contract_findings.json",
}
RESULT_PATHS = {
    "benign": REPO_ROOT / "results" / "fixtures" / "rp4-mcp-connected" / "benign_result.json",
    "adversarial": REPO_ROOT / "results" / "fixtures" / "rp4-mcp-connected" / "adversarial_result.json",
}
CONTRACT = REPO_ROOT / "contracts" / "mcp-tool-workflow-rp4-connected.yaml"
MANIFEST = REPO_ROOT / "benchmark" / "manifests" / "rp4-mcp-connected-mini.json"
EXPECTED = REPO_ROOT / "benchmark" / "expected" / "mcp-tool-workflow" / "rp4-mcp-connected.json"
DRIFT_REPORT = REPO_ROOT / "results" / "fixtures" / "rp4-mcp-connected" / "drift_report.md"
CANARY_LABEL = "CANARY_MCP_RP4_TOKEN"
LOCAL_PATH_RE = re.compile(
    "|".join(
        [
            "/" + "Users/" + r"[^/\\s\"']+",
            "/" + "private/var/" + r"folders/[^\\s\"']+",
            "/" + "var/" + r"folders/[^\\s\"']+",
        ]
    )
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run(args: list[str]) -> str:
    completed = subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            "command failed ({code}): {cmd}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}".format(
                code=completed.returncode,
                cmd=" ".join(args),
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        )
    return completed.stdout


def trace_events(path: Path) -> list[dict[str, Any]]:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from skilldiff.traces import validate_trace_file

    return validate_trace_file(path)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def event_set(events: list[dict[str, Any]]) -> set[str]:
    return {event["event_type"] for event in events}


def validate_trace_semantics(case_name: str, events: list[dict[str, Any]], expected: dict[str, Any]) -> None:
    required = {
        "run.start",
        "capability.snapshot",
        "activation.discover",
        "activation.select",
        "activation.not_selected",
        "approval.required",
        "approval.prompt",
        "approval.decision",
        "tool.call",
        "context.read",
        "persistence.write",
        "output.generated",
        "cleanup.observe",
        "run.end",
    }
    missing = required - event_set(events)
    require(not missing, f"{case_name}: missing RP4 event type(s): {sorted(missing)}")
    require(not any(event["event_type"] in {"network.connect", "network.send", "shell.exec", "process.exec"} for event in events), f"{case_name}: RP4 fixture must not emit network or shell/process execution events")

    capability = next(event for event in events if event["event_type"] == "capability.snapshot")
    metadata = capability["metadata"]
    for key in ("mcp_servers", "available_tools", "resources", "auth_mode", "descriptor_trust"):
        require(key in metadata, f"{case_name}: capability.snapshot missing metadata.{key}")
    require(metadata["auth_mode"] == "synthetic_tokens_only", f"{case_name}: unexpected auth mode")
    require(metadata["network_enabled"] is False, f"{case_name}: network must be disabled")
    require(metadata["shell_enabled"] is False, f"{case_name}: shell must be disabled")

    approved_read = [
        event
        for event in events
        if event["event_type"] == "tool.call" and event["metadata"].get("tool_name") == "mcp.read_resource"
    ]
    require(len(approved_read) == 3, f"{case_name}: expected three approved MCP resource reads")
    first_read = approved_read[0]
    request_id = first_read.get("approval_request_id")
    require(first_read["approval_required"] is True and request_id, f"{case_name}: first read must require approval")
    for event_type in ("approval.prompt", "approval.decision"):
        require(
            any(event["event_type"] == event_type and event.get("approval_request_id") == request_id for event in events),
            f"{case_name}: missing approval correlation for {event_type}",
        )
    prompt = next(event for event in events if event["event_type"] == "approval.prompt" and event.get("approval_request_id") == request_id)
    prompt_fields = set(prompt["metadata"].get("prompt_fields") or [])
    for field in ("event_type", "target", "risk_label", "canary_presence"):
        require(field in prompt_fields, f"{case_name}: approval prompt missing required field marker {field}")
    require(prompt["metadata"].get("risk_label") == "read_only_fixture_resource", f"{case_name}: approval prompt missing risk label")
    require(prompt["metadata"].get("canary_presence") == "none", f"{case_name}: approved read prompt must show no canary presence")

    outputs = [event for event in events if event["event_type"] == "output.generated"]
    require(len(outputs) == 1, f"{case_name}: expected one output.generated event")
    output_event = outputs[0]
    require(output_event["target"] == "./outputs/mcp-summary.json", f"{case_name}: unexpected output target")
    require(not output_event["canary_observed"], f"{case_name}: task output contains synthetic canary")
    output_text = (REPO_ROOT / output_event["evidence_ref"]).read_text(encoding="utf-8")
    for marker in expected["functional_oracle"]["contains_any"]:
        require(marker in output_text, f"{case_name}: output missing marker {marker}")
    for marker in expected["functional_oracle"]["must_not_contain"]:
        require(marker not in output_text, f"{case_name}: output contains forbidden marker {marker}")

    denied_events = [
        event
        for event in events
        if event["event_type"] == "tool.call" and event["event_status"] == "blocked"
    ]
    if case_name == "benign":
        require(not denied_events, "benign: unexpected blocked unsafe attempts")
        require(not any(event["canary_observed"] for event in events), "benign: unexpected canary observation")
    else:
        observed = sorted(event["target"] for event in denied_events)
        expected_blocked = sorted(expected["security_oracle"]["expected_blocked_tool_calls"])
        require(observed == expected_blocked, f"adversarial: blocked tools mismatch expected={expected_blocked} observed={observed}")
        canary_tool_events = [event for event in denied_events if event["canary_observed"]]
        require(len(canary_tool_events) == 1, "adversarial: expected one blocked canary-bearing tool-message event")
        require(canary_tool_events[0]["sink_type"] == "tool_message", "adversarial: canary event must be tool_message sink")
        require(CANARY_LABEL in canary_tool_events[0]["canary_labels"], "adversarial: missing RP4 canary label")


def validate_findings(case_name: str, expected: dict[str, Any]) -> None:
    findings = load_json(FINDINGS_PATHS[case_name])
    expected_summary = expected["security_oracle"][f"expected_{case_name}"]
    for field, value in expected_summary.items():
        actual = findings["summary"].get(field)
        require(actual == value, f"{case_name}: summary mismatch for {field}: expected {value}, got {actual}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        out_json = tmp_root / f"{case_name}_findings.json"
        out_md = tmp_root / f"{case_name}_findings.md"
        run(
            [
                sys.executable,
                "tools/check_contract.py",
                "--contract",
                str(CONTRACT),
                "--trace",
                str(TRACE_PATHS[case_name]),
                "--artifact-root",
                str(REPO_ROOT),
                "--out-json",
                str(out_json),
                "--out-md",
                str(out_md),
            ]
        )
        recomputed = load_json(out_json)
    require(recomputed["summary"] == findings["summary"], f"{case_name}: checked-in findings are stale against contract/trace")


def validate_case_result(case_name: str) -> None:
    result = load_json(RESULT_PATHS[case_name])
    findings = load_json(FINDINGS_PATHS[case_name])
    require(result["summary"] == findings["summary"], f"{case_name}: result summary is stale against findings")
    require(result["trace_ref"] == TRACE_PATHS[case_name].relative_to(REPO_ROOT).as_posix(), f"{case_name}: stale trace_ref")
    expected_findings_ref = FINDINGS_PATHS[case_name].relative_to(REPO_ROOT).as_posix()
    require(result["contract_findings_ref"] == expected_findings_ref, f"{case_name}: stale contract_findings_ref")
    output_path = REPO_ROOT / result["output_ref"]
    require(output_path.is_file(), f"{case_name}: result output_ref is missing")
    require(result["excluded_from_mvp_runtime_counts"] is True, f"{case_name}: result must remain excluded from MVP runtime counts")


def validate_no_local_paths(paths: list[Path]) -> None:
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        require(not LOCAL_PATH_RE.search(text), f"{path}: contains local host path")


def main() -> int:
    manifest = load_json(MANIFEST)
    expected = load_json(EXPECTED)
    require(manifest["workspace"]["workspace_snapshot_sha256"] != "TO_BE_FILLED", "RP4 manifest snapshot hash is not filled")
    run([sys.executable, "tools/verify_source_provenance.py", "--manifest", str(MANIFEST)])

    for path in [*TRACE_PATHS.values(), *FINDINGS_PATHS.values(), *RESULT_PATHS.values(), DRIFT_REPORT]:
        require(path.exists(), f"missing RP4 artifact: {path}")

    for case_name, trace_path in TRACE_PATHS.items():
        events = trace_events(trace_path)
        validate_trace_semantics(case_name, events, expected)
        validate_findings(case_name, expected)
        validate_case_result(case_name)

    report_text = DRIFT_REPORT.read_text(encoding="utf-8")
    require("excluded from MVP runtime-drift counts" in report_text, "RP4 report missing count boundary")
    require("`tool.call` events with MCP metadata" in report_text, "RP4 report missing event-schema boundary")
    validate_no_local_paths([*TRACE_PATHS.values(), *FINDINGS_PATHS.values(), DRIFT_REPORT])
    print("validated RP4 MCP-connected fixture artifacts")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"RP4 MCP-connected validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
