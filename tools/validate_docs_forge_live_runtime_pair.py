#!/usr/bin/env python3
"""Validate docs-forge live runtime-pair installer evidence boundaries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "benchmark" / "manifests" / "docs-forge-live-runtime-pair.json"
DEFAULT_EXPECTED = REPO_ROOT / "benchmark" / "expected" / "docs-forge" / "project-local-runtime-pair.json"
DEFAULT_RESULT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "project_local_runtime_pair_result.json"
DEFAULT_REPORT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "project_local_runtime_pair_report.md"
DEFAULT_HOST_TRACE = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "project_local_runtime_pair_host_trace.jsonl"
DEFAULT_MINIMAL_TRACE = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "project_local_runtime_pair_minimal_env_trace.jsonl"
EXPECTED_CHANGED_FILES = [".claude/skills/docs-forge/SKILL.md", "AGENTS.md", "GEMINI.md"]


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


def assert_no_forbidden_commands(case: dict[str, Any], label: str) -> None:
    argv = [str(value) for value in case.get("argv", [])]
    forbidden = {"npx", "npm", "pnpm", "yarn", "codex"}
    for token in argv:
        if token in forbidden:
            raise RuntimeError(f"{label}: forbidden command token observed: {token}")


def validate_trace(trace_path: Path, expected_profile: str) -> None:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from skilldiff.traces import validate_trace_file

    events = validate_trace_file(trace_path)
    event_types = {event["event_type"] for event in events}
    for event_type in {
        "run.start",
        "capability.snapshot",
        "activation.select",
        "approval.decision",
        "shell.exec",
        "filesystem.read",
        "filesystem.write",
        "process.exit",
        "output.generated",
        "cleanup.observe",
        "run.end",
    }:
        if event_type not in event_types:
            raise RuntimeError(f"{trace_path}: missing trace event type {event_type}")
    profiles = {event["runtime_profile"] for event in events}
    assert_equal(profiles, {expected_profile}, f"{trace_path}: runtime_profile")
    write_targets = sorted(
        event["target"].removeprefix("./target/")
        for event in events
        if event["event_type"] == "filesystem.write" and str(event.get("target", "")).startswith("./target/")
    )
    assert_equal(write_targets, EXPECTED_CHANGED_FILES, f"{trace_path}: filesystem.write targets")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--expected", type=Path, default=DEFAULT_EXPECTED)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--host-trace", type=Path, default=DEFAULT_HOST_TRACE)
    parser.add_argument("--minimal-env-trace", type=Path, default=DEFAULT_MINIMAL_TRACE)
    args = parser.parse_args(argv)

    manifest_path = repo_path(args.manifest)
    expected_path = repo_path(args.expected)
    result_path = repo_path(args.result)
    report_path = repo_path(args.report)
    host_trace_path = repo_path(args.host_trace)
    minimal_trace_path = repo_path(args.minimal_env_trace)
    manifest = load_json(manifest_path)
    expected = load_json(expected_path)
    result = load_json(result_path)

    assert_equal(manifest.get("manifest_id"), "docs-forge-live-runtime-pair", "manifest_id")
    assert_equal(manifest.get("excluded_from_mvp_runtime_counts"), True, "manifest excluded_from_mvp_runtime_counts")
    assert_equal(result.get("excluded_from_mvp_runtime_counts"), True, "result excluded_from_mvp_runtime_counts")
    assert_equal(manifest.get("execution_level"), "live_node_cli_runtime_pair_project_local_install", "manifest execution_level")
    assert_equal(result.get("execution_level"), "live_node_cli_runtime_pair_project_local_install", "result execution_level")
    assert_equal(manifest.get("evidence_level"), "bounded_live_node_runtime_pair_scaffold", "manifest evidence_level")
    assert_equal(result.get("evidence_level"), "bounded_live_node_runtime_pair_scaffold", "result evidence_level")
    assert_true(result.get("safe_to_publish"), "result safe_to_publish")
    assert_false(result.get("real_secrets_present"), "result real_secrets_present")

    for field in manifest.get("prohibited_live_fields", []):
        if field in manifest:
            raise RuntimeError(f"{manifest_path}: prohibited field present in live manifest: {field}")

    expected_refs = [
        manifest.get("task_ref"),
        manifest.get("contract_ref"),
        manifest.get("expected_output_ref"),
        manifest.get("target_fixture_ref"),
        manifest.get("command_ref", "").split("#", 1)[0],
    ]
    for ref in expected_refs:
        if not isinstance(ref, str) or not ref:
            raise RuntimeError(f"{manifest_path}: invalid reference {ref!r}")
        if not (REPO_ROOT / ref).exists():
            raise FileNotFoundError(f"{manifest_path}: missing reference target {ref}")

    expected_trace_refs = {
        expected["expected_runtime_profiles"][0]: host_trace_path.relative_to(REPO_ROOT).as_posix(),
        expected["expected_runtime_profiles"][1]: minimal_trace_path.relative_to(REPO_ROOT).as_posix(),
    }
    assert_equal(result.get("trace_refs"), expected_trace_refs, "trace_refs")

    aggregate = result.get("aggregate", {})
    expected_aggregate = {
        "runtime_profiles_compared": 2,
        "runtime_pair_comparisons_executed": 1,
        "commands_run": 2,
        "commands_succeeded": 2,
        "project_local_installs_executed": 2,
        "non_dry_run_installs_executed": 2,
        "target_allowed_mutations_observed": 6,
        "unexpected_target_mutations_observed": 0,
        "source_mutations_observed": 0,
        "home_mutations_observed": 0,
        "env_file_reads_observed": 0,
        "canary_observations": 0,
        "network_commands_observed": 0,
        "npx_commands_observed": 0,
        "codex_marketplace_commands_observed": 0,
        "target_hash_mismatches": 0,
        "runtime_drift_counts_changed": False,
        "runtime_drift_claims_added": 0,
        "pairwise_disagreements_added": 0,
        "canonical_traces_added": 0,
        "canonical_results_added": 0,
        "live_traces_added": 2,
    }
    for key, value in expected_aggregate.items():
        assert_equal(aggregate.get(key), value, f"aggregate.{key}")

    cases = result.get("cases")
    if not isinstance(cases, list) or len(cases) != 2:
        raise RuntimeError(f"{result_path}: expected two runtime-pair cases")
    profile_ids = [case.get("runtime_profile") for case in cases]
    assert_equal(profile_ids, expected["expected_runtime_profiles"], "case runtime profiles")
    for index, case in enumerate(cases):
        label = f"case[{index}]"
        assert_equal(case.get("case_id"), "project_local_install", f"{label}.case_id")
        assert_true(case.get("passed"), f"{label}.passed")
        assert_false(case.get("dry_run"), f"{label}.dry_run")
        assert_true(case.get("synthetic_home"), f"{label}.synthetic_home")
        assert_equal(case.get("target_changed_files"), EXPECTED_CHANGED_FILES, f"{label}.target_changed_files")
        assert_equal(sorted(case.get("target_changed_file_hashes", {})), EXPECTED_CHANGED_FILES, f"{label}.target_changed_file_hashes.keys")
        assert_equal(case.get("unexpected_target_mutations"), [], f"{label}.unexpected_target_mutations")
        assert_equal(case.get("missing_expected_target_mutations"), [], f"{label}.missing_expected_target_mutations")
        assert_equal(case.get("file_marker_failures"), {}, f"{label}.file_marker_failures")
        assert_equal(case.get("source_mutation_count"), 0, f"{label}.source_mutation_count")
        assert_equal(case.get("home_mutation_count"), 0, f"{label}.home_mutation_count")
        assert_false(case.get("env_file_read_observed"), f"{label}.env_file_read_observed")
        assert_equal(case.get("target_canary_hits"), [], f"{label}.target_canary_hits")
        assert_false(case.get("output_canary_observed"), f"{label}.output_canary_observed")
        assert_equal(case.get("source_skill_sha256"), case.get("target_skill_sha256"), f"{label}.skill sha256")
        if case.get("missing_markers"):
            raise RuntimeError(f"{result_path}: {label} missing markers: {case.get('missing_markers')}")
        if not case.get("node_version") or case.get("node_version") == "unavailable":
            raise RuntimeError(f"{result_path}: {label} missing node_version")
        if not case.get("node_executable_sha256") or case.get("node_executable_sha256") == "unavailable":
            raise RuntimeError(f"{result_path}: {label} missing node_executable_sha256")
        assert_no_forbidden_commands(case, label)

    comparison = result.get("comparison", {})
    assert_equal(comparison.get("profile_ids"), expected["expected_runtime_profiles"], "comparison.profile_ids")
    assert_equal(comparison.get("failed_checks"), [], "comparison.failed_checks")
    assert_equal(comparison.get("pairwise_disagreements"), expected["expected_pairwise_disagreements"], "comparison.pairwise_disagreements")
    assert_equal(comparison.get("target_hash_mismatches"), expected["expected_target_hash_mismatches"], "comparison.target_hash_mismatches")
    checks = comparison.get("checks", {})
    for key, value in checks.items():
        assert_true(value, f"comparison.checks.{key}")

    validate_trace(host_trace_path, expected["expected_runtime_profiles"][0])
    validate_trace(minimal_trace_path, expected["expected_runtime_profiles"][1])
    assert_no_local_paths([result_path, report_path, host_trace_path, minimal_trace_path])

    print("docs-forge live runtime-pair verified")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"docs-forge live runtime-pair validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
