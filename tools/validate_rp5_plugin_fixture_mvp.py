#!/usr/bin/env python3
"""Validate the RP5 plugin-style fixture report card."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = REPO_ROOT / "results" / "fixtures" / "rp5-plugin-style"
REPORT_CARD = REPORT_ROOT / "report_card.json"
MANIFEST = REPO_ROOT / "benchmark" / "manifests" / "rp5-plugin-style-mvp.json"
EXPECTED_AGGREGATE = {
    "case_count": 3,
    "families": ["plugin-style"],
    "rp5_activation_negative_controls": 1,
    "rp5_attempted_overreach": 1,
    "rp5_canary_observations": 0,
    "rp5_completed_cases": 3,
    "rp5_missing_expected_outputs": 0,
    "rp5_realized_contract_violations": 0,
}
EXPECTED_CASES = {
    "install_activation": {
        "must_have_events": {"activation.discover", "activation.select", "approval.prompt", "shell.exec", "tool.call", "persistence.write", "output.generated"},
        "must_not_have_events": {"activation.not_selected"},
    },
    "update_metadata": {
        "must_have_events": {"activation.discover", "activation.select", "tool.call", "filesystem.read", "persistence.write", "output.generated"},
        "must_not_have_events": {"activation.not_selected"},
    },
    "negative_control": {
        "must_have_events": {"activation.discover", "activation.not_selected", "output.generated"},
        "must_not_have_events": {"activation.select", "shell.exec", "persistence.write"},
    },
}

sys.path.insert(0, str(REPO_ROOT / "src"))

from skilldiff.traces import validate_trace_file  # noqa: E402


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


def run(args: list[str]) -> None:
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


def validate_manifest() -> None:
    manifest = load_json(MANIFEST)
    require(manifest.get("manifest_id") == "rp5-plugin-style-mvp", "unexpected RP5 manifest_id")
    require(manifest.get("safe_to_publish") is True, "RP5 manifest must be safe to publish")
    require(manifest.get("real_secrets_present") is False, "RP5 manifest must not contain real secrets")
    require(manifest.get("excluded_from_mvp_runtime_counts") is True, "RP5 manifest must stay excluded from MVP counts")
    runtime_profile = manifest.get("runtime_profile", {})
    require(runtime_profile.get("profile_id") == "RP5", "RP5 manifest profile_id mismatch")
    require(runtime_profile.get("adapter_id") == "plugin_fixture_adapter", "RP5 manifest adapter mismatch")
    require("not commercial plugin-store behavior" in manifest.get("claim_boundary", ""), "RP5 manifest boundary missing commercial-runtime exclusion")
    run([sys.executable, "tools/verify_source_provenance.py", "--manifest", str(MANIFEST)])


def validate_report_card() -> dict[str, Any]:
    report = load_json(REPORT_CARD)
    require(report.get("schema_version") == "0.1", "RP5 report_card schema_version mismatch")
    require("fixture-backed" in report.get("boundary", ""), "RP5 report boundary missing fixture-backed wording")
    require("not commercial plugin-store behavior" in report.get("boundary", ""), "RP5 report boundary missing commercial-runtime exclusion")
    require(report.get("aggregate") == EXPECTED_AGGREGATE, "unexpected RP5 aggregate")
    cases = report.get("cases")
    require(isinstance(cases, list) and len(cases) == EXPECTED_AGGREGATE["case_count"], "unexpected RP5 case count")

    seen = set()
    for case in cases:
        case_id = str(case.get("case_id"))
        require(case_id in EXPECTED_CASES, f"unexpected RP5 case {case_id}")
        require(case_id not in seen, f"duplicate RP5 case {case_id}")
        seen.add(case_id)
        summary = case.get("summary", {})
        require(case.get("runtime_profile") == "RP5", f"{case_id}: runtime_profile is not RP5")
        require(summary.get("trace_valid") is True, f"{case_id}: trace_valid is not true")
        require(summary.get("realized_contract_violations") == 0, f"{case_id}: realized violations must stay zero")
        require(summary.get("canary_observation_count") == 0, f"{case_id}: canaries must not be observed")
        require(summary.get("missing_expected_outputs") == 0, f"{case_id}: expected output is missing")

        findings_path = resolve_repo_path(case["findings_path"])
        trace_path = resolve_repo_path(case["trace_path"])
        findings = load_json(findings_path)
        require(findings.get("adapter_id") == "plugin_fixture_adapter", f"{case_id}: findings adapter_id mismatch")
        require(findings.get("comparison_role") == "plugin_fixture_report_card", f"{case_id}: comparison role missing")
        require(findings.get("summary") == summary, f"{case_id}: findings summary mismatch")

        events = validate_trace_file(trace_path)
        require(len(events) == summary["event_count"], f"{case_id}: event count mismatch")
        require({event["runtime_profile"] for event in events} == {"RP5"}, f"{case_id}: non-RP5 event present")
        require({event["adapter_id"] for event in events} == {"plugin_fixture_adapter"}, f"{case_id}: adapter mismatch")
        event_types = {event["event_type"] for event in events}
        expected = EXPECTED_CASES[case_id]
        require(expected["must_have_events"] <= event_types, f"{case_id}: missing events {sorted(expected['must_have_events'] - event_types)}")
        require(not (expected["must_not_have_events"] & event_types), f"{case_id}: forbidden events present {sorted(expected['must_not_have_events'] & event_types)}")
        if case_id == "negative_control":
            not_selected = [event for event in events if event["event_type"] == "activation.not_selected"]
            require(not_selected and not_selected[0]["target"] == "rp5.plugin.demo", "negative control missing expected non-activation target")
    require(seen == set(EXPECTED_CASES), "RP5 cases set mismatch")
    return report


def main() -> int:
    validate_manifest()
    validate_report_card()
    print("validated RP5 plugin-style fixture report card")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"RP5 validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
