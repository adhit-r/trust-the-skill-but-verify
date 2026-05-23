#!/usr/bin/env python3
"""Validate docs-forge live npx runtime-pair scaffold evidence boundaries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "benchmark" / "manifests" / "docs-forge-live-npx-runtime-pair.json"
DEFAULT_EXPECTED = REPO_ROOT / "benchmark" / "expected" / "docs-forge" / "npx-runtime-pair.json"
DEFAULT_RESULT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_runtime_pair_result.json"
DEFAULT_REPORT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_runtime_pair_report.md"
DEFAULT_RP2_RESULT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_runtime_pair_rp2_result.json"
DEFAULT_RP2_REPORT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_runtime_pair_rp2_report.md"
DEFAULT_RP2_TRACE = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_runtime_pair_rp2_trace.jsonl"
DEFAULT_RP3_RESULT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_runtime_pair_rp3_result.json"
DEFAULT_RP3_REPORT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_runtime_pair_rp3_report.md"
DEFAULT_RP3_TRACE = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_runtime_pair_rp3_trace.jsonl"


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


def validate_trace(trace_path: Path, expected_profile: str) -> None:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from skilldiff.traces import validate_trace_file

    events = validate_trace_file(trace_path)
    profiles = {event["runtime_profile"] for event in events}
    assert_equal(profiles, {expected_profile}, f"{trace_path}: runtime_profile")
    event_types = {event["event_type"] for event in events}
    for event_type in {"run.start", "capability.snapshot", "activation.select", "approval.decision", "shell.exec", "filesystem.read", "filesystem.write", "process.exit", "output.generated", "cleanup.observe", "run.end"}:
        if event_type not in event_types:
            raise RuntimeError(f"{trace_path}: missing trace event type {event_type}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--expected", type=Path, default=DEFAULT_EXPECTED)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--rp2-result", type=Path, default=DEFAULT_RP2_RESULT)
    parser.add_argument("--rp2-report", type=Path, default=DEFAULT_RP2_REPORT)
    parser.add_argument("--rp2-trace", type=Path, default=DEFAULT_RP2_TRACE)
    parser.add_argument("--rp3-result", type=Path, default=DEFAULT_RP3_RESULT)
    parser.add_argument("--rp3-report", type=Path, default=DEFAULT_RP3_REPORT)
    parser.add_argument("--rp3-trace", type=Path, default=DEFAULT_RP3_TRACE)
    args = parser.parse_args(argv)

    manifest_path = repo_path(args.manifest)
    expected_path = repo_path(args.expected)
    result_path = repo_path(args.result)
    report_path = repo_path(args.report)
    rp2_result_path = repo_path(args.rp2_result)
    rp2_report_path = repo_path(args.rp2_report)
    rp2_trace_path = repo_path(args.rp2_trace)
    rp3_result_path = repo_path(args.rp3_result)
    rp3_report_path = repo_path(args.rp3_report)
    rp3_trace_path = repo_path(args.rp3_trace)
    manifest = load_json(manifest_path)
    expected = load_json(expected_path)
    result = load_json(result_path)
    rp2_result = load_json(rp2_result_path)
    rp3_result = load_json(rp3_result_path)

    assert_equal(manifest.get("manifest_id"), "docs-forge-live-npx-runtime-pair", "manifest_id")
    assert_equal(manifest.get("excluded_from_mvp_runtime_counts"), True, "manifest excluded_from_mvp_runtime_counts")
    assert_equal(result.get("excluded_from_mvp_runtime_counts"), True, "result excluded_from_mvp_runtime_counts")
    assert_equal(manifest.get("execution_level"), "live_node_cli_local_tarball_npx_runtime_pair_scaffold", "manifest execution_level")
    assert_equal(result.get("execution_level"), "live_node_cli_local_tarball_npx_runtime_pair_scaffold", "result execution_level")
    assert_equal(manifest.get("evidence_level"), "bounded_local_tarball_npx_pair_comparison", "manifest evidence_level")
    assert_equal(result.get("evidence_level"), "bounded_local_tarball_npx_pair_comparison", "result evidence_level")
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
    assert_equal(rp2_result.get("runtime_profile"), profiles[0], "rp2 runtime_profile")
    assert_equal(rp3_result.get("runtime_profile"), profiles[1], "rp3 runtime_profile")
    child_refs = result.get("child_result_refs", {})
    assert_equal(child_refs[profiles[0]]["json"], rp2_result_path.relative_to(REPO_ROOT).as_posix(), "rp2 child json ref")
    assert_equal(child_refs[profiles[0]]["trace"], rp2_trace_path.relative_to(REPO_ROOT).as_posix(), "rp2 child trace ref")
    assert_equal(child_refs[profiles[1]]["json"], rp3_result_path.relative_to(REPO_ROOT).as_posix(), "rp3 child json ref")
    assert_equal(child_refs[profiles[1]]["trace"], rp3_trace_path.relative_to(REPO_ROOT).as_posix(), "rp3 child trace ref")

    cases = result.get("cases")
    if not isinstance(cases, list) or len(cases) != 2:
        raise RuntimeError(f"{result_path}: expected two cases")
    for index, case in enumerate(cases):
        label = f"case[{index}]"
        assert_true(case.get("passed"), f"{label}.passed")
        assert_equal(case.get("npx_exit_code"), expected["expected_exit_code"], f"{label}.npx_exit_code")
        assert_equal(case.get("package_name"), expected["expected_package"]["name"], f"{label}.package_name")
        assert_equal(case.get("package_version"), expected["expected_package"]["version"], f"{label}.package_version")
        assert_equal(case.get("package_filename"), expected["expected_package"]["filename"], f"{label}.package_filename")
        assert_equal(case.get("package_entry_count"), expected["expected_package"]["entry_count"], f"{label}.package_entry_count")
        assert_equal(case.get("missing_stdout_markers"), [], f"{label}.missing_stdout_markers")
        assert_equal(case.get("source_mutation_count"), expected["expected_source_mutations"], f"{label}.source_mutation_count")
        assert_equal(case.get("home_mutation_count"), expected["expected_home_mutations"], f"{label}.home_mutation_count")
        assert_false(case.get("registry_acquisition_executed"), f"{label}.registry_acquisition_executed")
        assert_false(case.get("package_install_executed"), f"{label}.package_install_executed")
        assert_false(case.get("lifecycle_scripts_executed"), f"{label}.lifecycle_scripts_executed")
        assert_equal(case.get("network_events_observed"), 0, f"{label}.network_events_observed")

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
        "commands_run": 5,
        "commands_succeeded": 5,
        "workload_commands_run": expected["expected_workload_commands"],
        "npx_commands_executed": expected["expected_npx_executions"],
        "npx_local_tarball_commands_executed": expected["expected_npx_executions"],
        "npx_package_name_commands_executed": 0,
        "registry_acquisitions_observed": expected["expected_registry_acquisitions"],
        "package_install_commands_executed": expected["expected_package_install_commands"],
        "lifecycle_scripts_executed": expected["expected_lifecycle_scripts_executed"],
        "package_tarballs_materialized": 2,
        "source_mutations_observed": 0,
        "synthetic_home_mutations_observed": 0,
        "network_events_observed": 0,
        "public_internet_contact_measured": False,
        "required_pair_checks_failed": 0,
        "runtime_drift_counts_changed": False,
        "runtime_drift_claims_added": expected["expected_runtime_drift_claims"],
        "pairwise_disagreements_added": 0,
        "canonical_traces_added": 0,
        "canonical_results_added": 0,
        "live_traces_added": expected["expected_live_traces"],
    }
    for key, value in expected_aggregate.items():
        assert_equal(aggregate.get(key), value, f"aggregate.{key}")

    validate_trace(rp2_trace_path, profiles[0])
    validate_trace(rp3_trace_path, profiles[1])
    assert_no_local_paths([result_path, report_path, rp2_result_path, rp2_report_path, rp2_trace_path, rp3_result_path, rp3_report_path, rp3_trace_path])

    print("docs-forge live npx runtime-pair verified")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"docs-forge live npx runtime-pair validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
