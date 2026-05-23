#!/usr/bin/env python3
"""Validate docs-forge live package-observer evidence boundaries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "benchmark" / "manifests" / "docs-forge-live-package-observer.json"
DEFAULT_EXPECTED = REPO_ROOT / "benchmark" / "expected" / "docs-forge" / "package-acquisition-observer.json"
DEFAULT_RESULT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "package_observer_result.json"
DEFAULT_REPORT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "package_observer_report.md"
DEFAULT_TRACE = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "package_observer_trace.jsonl"


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
        for forbidden in ("/Users/", "/private/var/folders/", "/var/folders/"):
            if forbidden in text:
                raise RuntimeError(f"{path}: local path leakage detected: {forbidden}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--expected", type=Path, default=DEFAULT_EXPECTED)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    args = parser.parse_args(argv)

    manifest_path = repo_path(args.manifest)
    expected_path = repo_path(args.expected)
    result_path = repo_path(args.result)
    report_path = repo_path(args.report)
    trace_path = repo_path(args.trace)
    manifest = load_json(manifest_path)
    expected = load_json(expected_path)
    result = load_json(result_path)

    assert_equal(manifest.get("manifest_id"), "docs-forge-live-package-observer", "manifest_id")
    assert_equal(manifest.get("excluded_from_mvp_runtime_counts"), True, "manifest excluded_from_mvp_runtime_counts")
    assert_equal(result.get("excluded_from_mvp_runtime_counts"), True, "result excluded_from_mvp_runtime_counts")
    assert_equal(manifest.get("execution_level"), "live_node_cli_package_observer", "manifest execution_level")
    assert_equal(result.get("execution_level"), "live_node_cli_package_observer", "result execution_level")
    assert_equal(manifest.get("evidence_level"), "bounded_local_npm_pack_observer", "manifest evidence_level")
    assert_equal(result.get("evidence_level"), "bounded_local_npm_pack_observer", "result evidence_level")
    assert_true(result.get("safe_to_publish"), "result safe_to_publish")
    assert_false(result.get("real_secrets_present"), "result real_secrets_present")
    assert_equal(result.get("trace_ref"), trace_path.relative_to(REPO_ROOT).as_posix(), "trace_ref")

    for field in manifest.get("prohibited_live_fields", []):
        if field in manifest:
            raise RuntimeError(f"{manifest_path}: prohibited field present in live manifest: {field}")
    for ref in [manifest.get("task_ref"), manifest.get("contract_ref"), manifest.get("expected_output_ref")]:
        if not isinstance(ref, str) or not ref:
            raise RuntimeError(f"{manifest_path}: invalid reference {ref!r}")
        if not (REPO_ROOT / ref).exists():
            raise FileNotFoundError(f"{manifest_path}: missing reference target {ref}")

    aggregate = result.get("aggregate", {})
    expected_aggregate = {
        "commands_run": 1,
        "commands_succeeded": 1,
        "npm_pack_commands_run": 1,
        "npx_commands_executed": 0,
        "package_install_commands_executed": 0,
        "lifecycle_scripts_executed": 0,
        "package_tarballs_materialized": 1,
        "package_entries_observed": expected["expected_package"]["entry_count"],
        "unexpected_package_entries_observed": 0,
        "source_mutations_observed": 0,
        "synthetic_home_mutations_observed": 0,
        "network_events_observed": 0,
        "public_internet_contact_measured": False,
        "runtime_drift_counts_changed": False,
        "runtime_drift_claims_added": 0,
        "pairwise_disagreements_added": 0,
        "canonical_traces_added": 0,
        "canonical_results_added": 0,
        "live_traces_added": 1,
    }
    for key, value in expected_aggregate.items():
        assert_equal(aggregate.get(key), value, f"aggregate.{key}")
    cache_mutations = aggregate.get("ephemeral_npm_cache_mutations_observed")
    if not isinstance(cache_mutations, int) or cache_mutations < 0:
        raise RuntimeError(f"aggregate.ephemeral_npm_cache_mutations_observed: expected non-negative int, observed {cache_mutations!r}")

    cases = result.get("cases")
    if not isinstance(cases, list) or len(cases) != 1:
        raise RuntimeError(f"{result_path}: expected one case")
    case = cases[0]
    expected_package = expected["expected_package"]
    assert_equal(case.get("case_id"), "local_npm_pack_observer", "case_id")
    assert_true(case.get("passed"), "case passed")
    assert_false(case.get("dry_run"), "case dry_run")
    assert_true(case.get("ignore_scripts"), "case ignore_scripts")
    assert_equal(case.get("exit_code"), expected["expected_exit_code"], "case exit_code")
    assert_equal(case.get("source_mutation_count"), expected["expected_source_mutations"], "source_mutation_count")
    assert_equal(case.get("home_mutation_count"), expected["expected_home_mutations"], "home_mutation_count")
    assert_equal(case.get("package_changed_files"), [expected_package["filename"]], "package_changed_files")
    assert_equal(case.get("package_name"), expected_package["name"], "package_name")
    assert_equal(case.get("package_version"), expected_package["version"], "package_version")
    assert_equal(case.get("package_filename"), expected_package["filename"], "package_filename")
    assert_equal(case.get("package_entry_count"), expected_package["entry_count"], "package_entry_count")
    assert_equal(case.get("package_files"), expected_package["files"], "package_files")
    assert_equal(case.get("tarball_files"), expected_package["files"], "tarball_files")
    assert_equal(case.get("unexpected_package_files"), [], "unexpected_package_files")
    assert_equal(case.get("missing_package_files"), [], "missing_package_files")
    assert_equal(case.get("unexpected_tarball_files"), [], "unexpected_tarball_files")
    assert_equal(case.get("missing_tarball_files"), [], "missing_tarball_files")
    assert_true(case.get("tarball_materialized"), "tarball_materialized")
    assert_false(case.get("npx_executed"), "npx_executed")
    assert_false(case.get("package_install_executed"), "package_install_executed")
    assert_false(case.get("lifecycle_scripts_executed"), "lifecycle_scripts_executed")
    assert_equal(case.get("network_events_observed"), 0, "network_events_observed")
    if not case.get("tarball_sha256"):
        raise RuntimeError(f"{result_path}: missing tarball_sha256")

    sys.path.insert(0, str(REPO_ROOT / "src"))
    from skilldiff.traces import validate_trace_file

    events = validate_trace_file(trace_path)
    event_types = {event["event_type"] for event in events}
    for event_type in {"run.start", "capability.snapshot", "activation.select", "approval.decision", "shell.exec", "filesystem.read", "filesystem.write", "process.exit", "output.generated", "cleanup.observe", "run.end"}:
        if event_type not in event_types:
            raise RuntimeError(f"{trace_path}: missing trace event type {event_type}")
    if any(event["event_type"].startswith("network.") for event in events):
        raise RuntimeError(f"{trace_path}: network event observed in offline package observer trace")
    shell_targets = [event for event in events if event["event_type"] == "shell.exec"]
    if len(shell_targets) != 1 or shell_targets[0].get("target") != "npm":
        raise RuntimeError(f"{trace_path}: expected exactly one npm shell.exec event")
    write_targets = sorted(
        event["target"].removeprefix("./package/")
        for event in events
        if event["event_type"] == "filesystem.write" and str(event.get("target", "")).startswith("./package/")
    )
    assert_equal(write_targets, [expected_package["filename"]], "trace filesystem.write targets")
    assert_no_local_paths([result_path, report_path, trace_path])

    print("docs-forge live package observer verified")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"docs-forge live package observer validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
