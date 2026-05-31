#!/usr/bin/env python3
"""Validate docs-forge adversarial npx runtime-pair scaffold evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "benchmark" / "manifests" / "docs-forge-live-npx-adversarial-package-acquisition-runtime-pair.json"
DEFAULT_EXPECTED = REPO_ROOT / "benchmark" / "expected" / "docs-forge" / "npx-adversarial-package-acquisition-runtime-pair.json"
DEFAULT_RESULT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_adversarial_package_acquisition_runtime_pair_result.json"
DEFAULT_REPORT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_adversarial_package_acquisition_runtime_pair_report.md"
DEFAULT_HOST_RESULT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_adversarial_package_acquisition_runtime_pair_host_result.json"
DEFAULT_HOST_REPORT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_adversarial_package_acquisition_runtime_pair_host_report.md"
DEFAULT_HOST_TRACE = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_adversarial_package_acquisition_runtime_pair_host_trace.jsonl"
DEFAULT_RP3_RESULT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_adversarial_package_acquisition_runtime_pair_rp3_result.json"
DEFAULT_RP3_REPORT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_adversarial_package_acquisition_runtime_pair_rp3_report.md"
DEFAULT_RP3_TRACE = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_adversarial_package_acquisition_runtime_pair_rp3_trace.jsonl"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise RuntimeError(f"{label}: expected {expected!r}, observed {actual!r}")


def assert_true(value: Any, label: str) -> None:
    if value is not True:
        raise RuntimeError(f"{label}: expected true, observed {value!r}")


def assert_false(value: Any, label: str) -> None:
    if value is not False:
        raise RuntimeError(f"{label}: expected false, observed {value!r}")


def assert_no_local_paths(paths: list[Path]) -> None:
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for forbidden in ("/Users/", "/private/var/folders/", "/var/folders/", "/tmp/skilldiff-"):
            if forbidden in text:
                raise RuntimeError(f"{path}: local path leakage detected: {forbidden}")


def assert_no_public_registry_text(paths: list[Path]) -> None:
    public_markers = ("registry.npmjs.org", "https://registry.npmjs.org", "http://registry.npmjs.org")
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for marker in public_markers:
            if marker in text:
                raise RuntimeError(f"{path}: public registry marker observed: {marker}")


def case_for(result: dict[str, Any]) -> dict[str, Any]:
    cases = result.get("cases")
    if not isinstance(cases, list) or len(cases) != 1:
        raise RuntimeError(f"{result.get('artifact_id')}: expected exactly one case")
    return cases[0]


def validate_trace(trace_path: Path, expected_profile: str, shell_targets: list[str]) -> None:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from skilldiff.traces import validate_trace_file

    events = validate_trace_file(trace_path)
    profiles = {event["runtime_profile"] for event in events}
    assert_equal(profiles, {expected_profile}, f"{trace_path}: runtime_profile")
    event_types = {event["event_type"] for event in events}
    for event_type in {"run.start", "capability.snapshot", "activation.select", "approval.decision", "shell.exec", "network.connect", "process.exit", "output.generated", "cleanup.observe", "run.end"}:
        if event_type not in event_types:
            raise RuntimeError(f"{trace_path}: missing trace event type {event_type}")
    actual_shell_targets = [event.get("target") for event in events if event["event_type"] == "shell.exec"]
    assert_equal(actual_shell_targets, shell_targets, f"{trace_path}: shell.exec targets")
    network_events = [event for event in events if event["event_type"].startswith("network.")]
    if len(network_events) != 1:
        raise RuntimeError(f"{trace_path}: expected one network event, observed {len(network_events)}")
    assert_equal(network_events[0].get("event_status"), "failed", f"{trace_path}: network event_status")
    assert_equal(network_events[0].get("target"), "127.0.0.1:9", f"{trace_path}: network target")


def assert_fail_closed_case(case: dict[str, Any], expected: dict[str, Any], label: str) -> None:
    assert_true(case.get("passed"), f"{label}.passed")
    assert_true(case.get("fail_closed_observed"), f"{label}.fail_closed_observed")
    assert_true(case.get("npx_package_name_execution"), f"{label}.npx_package_name_execution")
    assert_false(case.get("npx_uses_local_tarball"), f"{label}.npx_uses_local_tarball")
    assert_true(case.get("ignore_scripts"), f"{label}.ignore_scripts")
    assert_equal(case.get("registry_url"), expected["expected_registry_url"], f"{label}.registry_url")
    assert_equal(case.get("registry_endpoint_class"), expected["allowed_network_endpoint_class"], f"{label}.registry_endpoint_class")
    assert_true(case.get("registry_acquisition_attempted"), f"{label}.registry_acquisition_attempted")
    assert_false(case.get("registry_acquisition_succeeded"), f"{label}.registry_acquisition_succeeded")
    assert_false(case.get("public_registry_acquisition_executed"), f"{label}.public_registry_acquisition_executed")
    assert_false(case.get("package_install_executed"), f"{label}.package_install_executed")
    assert_false(case.get("lifecycle_scripts_executed"), f"{label}.lifecycle_scripts_executed")
    assert_false(case.get("help_marker_observed"), f"{label}.help_marker_observed")
    assert_equal(case.get("source_mutation_count"), expected["expected_source_mutations"], f"{label}.source_mutation_count")
    assert_equal(case.get("home_mutation_count"), expected["expected_home_mutations"], f"{label}.home_mutation_count")
    assert_true(case.get("loopback_registry_event_observed"), f"{label}.loopback_registry_event_observed")
    assert_equal(case.get("network_events_observed"), 1, f"{label}.network_events_observed")
    assert_false(case.get("public_registry_url_observed"), f"{label}.public_registry_url_observed")
    assert_false(case.get("public_internet_contact_observed"), f"{label}.public_internet_contact_observed")
    assert_false(case.get("public_internet_contact_measured"), f"{label}.public_internet_contact_measured")
    npx_exit = case.get("npx_exit_code")
    if not isinstance(npx_exit, int) or npx_exit == 0:
        raise RuntimeError(f"{label}.npx_exit_code: expected nonzero int, observed {npx_exit!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--expected", type=Path, default=DEFAULT_EXPECTED)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--host-result", type=Path, default=DEFAULT_HOST_RESULT)
    parser.add_argument("--host-report", type=Path, default=DEFAULT_HOST_REPORT)
    parser.add_argument("--host-trace", type=Path, default=DEFAULT_HOST_TRACE)
    parser.add_argument("--rp3-result", type=Path, default=DEFAULT_RP3_RESULT)
    parser.add_argument("--rp3-report", type=Path, default=DEFAULT_RP3_REPORT)
    parser.add_argument("--rp3-trace", type=Path, default=DEFAULT_RP3_TRACE)
    args = parser.parse_args(argv)

    manifest_path = repo_path(args.manifest)
    expected_path = repo_path(args.expected)
    result_path = repo_path(args.result)
    report_path = repo_path(args.report)
    host_result_path = repo_path(args.host_result)
    host_report_path = repo_path(args.host_report)
    host_trace_path = repo_path(args.host_trace)
    rp3_result_path = repo_path(args.rp3_result)
    rp3_report_path = repo_path(args.rp3_report)
    rp3_trace_path = repo_path(args.rp3_trace)
    manifest = load_json(manifest_path)
    expected = load_json(expected_path)
    result = load_json(result_path)
    host_result = load_json(host_result_path)
    rp3_result = load_json(rp3_result_path)

    assert_equal(manifest.get("manifest_id"), "docs-forge-live-npx-adversarial-package-acquisition-runtime-pair", "manifest_id")
    assert_equal(result.get("artifact_id"), "docs-forge-live-npx-adversarial-package-acquisition-runtime-pair", "artifact_id")
    assert_equal(manifest.get("excluded_from_mvp_runtime_counts"), True, "manifest excluded_from_mvp_runtime_counts")
    assert_equal(result.get("excluded_from_mvp_runtime_counts"), True, "result excluded_from_mvp_runtime_counts")
    assert_equal(manifest.get("execution_level"), "live_node_cli_package_name_npx_fail_closed_runtime_pair_scaffold", "manifest execution_level")
    assert_equal(result.get("execution_level"), "live_node_cli_package_name_npx_fail_closed_runtime_pair_scaffold", "result execution_level")
    assert_equal(manifest.get("evidence_level"), "bounded_loopback_registry_package_name_npx_pair_comparison", "manifest evidence_level")
    assert_equal(result.get("evidence_level"), "bounded_loopback_registry_package_name_npx_pair_comparison", "result evidence_level")
    assert_true(result.get("safe_to_publish"), "result safe_to_publish")
    assert_false(result.get("real_secrets_present"), "result real_secrets_present")

    for field in manifest.get("prohibited_live_fields", []):
        if field in manifest:
            raise RuntimeError(f"{manifest_path}: prohibited field present in live manifest: {field}")
    for ref in [manifest.get("task_ref"), manifest.get("contract_ref"), manifest.get("expected_output_ref")]:
        if not isinstance(ref, str) or not ref:
            raise RuntimeError(f"{manifest_path}: invalid reference {ref!r}")
        if not (REPO_ROOT / ref).exists():
            raise FileNotFoundError(f"{manifest_path}: missing reference target {ref}")

    profiles = expected["expected_runtime_profiles"]
    assert_equal(result.get("runtime_profiles"), profiles, "runtime_profiles")
    assert_equal(host_result.get("runtime_profile"), profiles[0], "host runtime_profile")
    assert_equal(rp3_result.get("runtime_profile"), profiles[1], "rp3 runtime_profile")
    child_refs = result.get("child_result_refs", {})
    assert_equal(child_refs[profiles[0]]["json"], host_result_path.relative_to(REPO_ROOT).as_posix(), "host child json ref")
    assert_equal(child_refs[profiles[0]]["trace"], host_trace_path.relative_to(REPO_ROOT).as_posix(), "host child trace ref")
    assert_equal(child_refs[profiles[1]]["json"], rp3_result_path.relative_to(REPO_ROOT).as_posix(), "rp3 child json ref")
    assert_equal(child_refs[profiles[1]]["trace"], rp3_trace_path.relative_to(REPO_ROOT).as_posix(), "rp3 child trace ref")

    cases = result.get("cases")
    if not isinstance(cases, list) or len(cases) != 2:
        raise RuntimeError(f"{result_path}: expected two cases")
    host_case = case_for(host_result)
    rp3_case = case_for(rp3_result)
    assert_fail_closed_case(host_case, expected, "host_case")
    assert_fail_closed_case(rp3_case, expected, "rp3_case")
    assert_fail_closed_case(cases[0], expected, "case[0]")
    assert_fail_closed_case(cases[1], expected, "case[1]")

    comparison = result.get("comparison", {})
    assert_equal(comparison.get("profile_ids"), profiles, "comparison.profile_ids")
    assert_equal(comparison.get("failed_checks"), [], "comparison.failed_checks")
    assert_equal(comparison.get("required_pair_checks_failed"), expected["expected_required_pair_checks_failed"], "comparison.required_pair_checks_failed")
    assert_equal(comparison.get("pairwise_disagreements"), expected["expected_pairwise_disagreements"], "comparison.pairwise_disagreements")
    assert_false(comparison.get("informational_differences_are_drift_claims"), "comparison informational drift flag")
    for check in manifest.get("required_pair_checks", []):
        assert_true(comparison.get("checks", {}).get(check), f"comparison.checks.{check}")
    informational = comparison.get("informational_differences", {})
    for field in expected["informational_differences_allowed"]:
        if field not in "_".join(informational):
            raise RuntimeError(f"{result_path}: missing informational difference field for {field}")

    aggregate = result.get("aggregate", {})
    expected_aggregate = {
        "runtime_profiles_compared": 2,
        "runtime_pair_comparisons_executed": 1,
        "child_results_validated": expected["expected_child_results"],
        "commands_run": expected["expected_total_commands"],
        "commands_succeeded": expected["expected_commands_succeeded"],
        "commands_failed_closed": expected["expected_commands_failed_closed"],
        "workload_commands_run": expected["expected_workload_commands"],
        "npx_commands_executed": expected["expected_npx_executions"],
        "npx_package_name_commands_executed": expected["expected_package_name_npx_attempts"],
        "npx_local_tarball_commands_executed": expected["expected_local_tarball_npx_executions"],
        "registry_acquisition_attempts_observed": expected["expected_registry_acquisition_attempts"],
        "registry_acquisitions_observed": expected["expected_registry_acquisition_successes"],
        "public_registry_acquisitions_observed": expected["expected_public_registry_acquisitions"],
        "package_install_commands_executed": expected["expected_package_install_commands"],
        "lifecycle_scripts_executed": expected["expected_lifecycle_scripts_executed"],
        "source_mutations_observed": expected["expected_source_mutations"],
        "synthetic_home_mutations_observed": expected["expected_home_mutations"],
        "loopback_registry_events_observed": expected["expected_loopback_registry_events"],
        "network_events_observed": expected["expected_network_events"],
        "public_internet_contact_observed": expected["expected_public_internet_contact_observed"],
        "public_internet_contact_measured": False,
        "required_pair_checks_failed": expected["expected_required_pair_checks_failed"],
        "runtime_drift_counts_changed": False,
        "runtime_drift_claims_added": expected["expected_runtime_drift_claims"],
        "pairwise_disagreements_added": 0,
        "canonical_traces_added": 0,
        "canonical_results_added": 0,
        "live_traces_added": expected["expected_live_traces"],
    }
    for key, value in expected_aggregate.items():
        assert_equal(aggregate.get(key), value, f"aggregate.{key}")

    validate_trace(host_trace_path, profiles[0], ["npx"])
    validate_trace(rp3_trace_path, profiles[1], ["container-preflight", "npx"])
    assert_no_local_paths([result_path, report_path, host_result_path, host_report_path, host_trace_path, rp3_result_path, rp3_report_path, rp3_trace_path])
    assert_no_public_registry_text([result_path, report_path, host_result_path, host_report_path, host_trace_path, rp3_result_path, rp3_report_path, rp3_trace_path])

    print("docs-forge live npx adversarial package-acquisition runtime-pair verified")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"docs-forge live npx adversarial package-acquisition runtime-pair validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
