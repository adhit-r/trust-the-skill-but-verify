#!/usr/bin/env python3
"""Validate docs-forge live project-local installer evidence boundaries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "benchmark" / "manifests" / "docs-forge-live-project-local-install.json"
DEFAULT_RESULT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "project_local_install_result.json"
DEFAULT_REPORT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "project_local_install_report.md"
DEFAULT_TRACE = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "project_local_install_trace.jsonl"


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
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    args = parser.parse_args(argv)

    manifest_path = repo_path(args.manifest)
    result_path = repo_path(args.result)
    report_path = repo_path(args.report)
    trace_path = repo_path(args.trace)
    manifest = load_json(manifest_path)
    result = load_json(result_path)

    assert_equal(manifest.get("excluded_from_mvp_runtime_counts"), True, "manifest excluded_from_mvp_runtime_counts")
    assert_equal(result.get("excluded_from_mvp_runtime_counts"), True, "result excluded_from_mvp_runtime_counts")
    assert_equal(manifest.get("execution_level"), "live_node_cli_project_local_install", "manifest execution_level")
    assert_equal(result.get("execution_level"), "live_node_cli_project_local_install", "result execution_level")
    assert_true(result.get("safe_to_publish"), "result safe_to_publish")
    assert_false(result.get("real_secrets_present"), "result real_secrets_present")
    assert_equal(result.get("trace_ref"), trace_path.relative_to(REPO_ROOT).as_posix(), "result trace_ref")

    for field in manifest.get("prohibited_live_fields", []):
        if field in manifest:
            raise RuntimeError(f"{manifest_path}: prohibited field present in live manifest: {field}")

    expected_refs = [
        manifest.get("task_ref"),
        manifest.get("contract_ref"),
        manifest.get("expected_output_ref"),
        manifest.get("target_fixture_ref"),
    ]
    for ref in expected_refs:
        if not isinstance(ref, str) or not ref:
            raise RuntimeError(f"{manifest_path}: invalid reference {ref!r}")
        if not (REPO_ROOT / ref).exists():
            raise FileNotFoundError(f"{manifest_path}: missing reference target {ref}")

    aggregate = result.get("aggregate", {})
    expected_aggregate = {
        "commands_run": 1,
        "commands_succeeded": 1,
        "project_local_installs_executed": 1,
        "non_dry_run_installs_executed": 1,
        "target_allowed_mutations_observed": 3,
        "unexpected_target_mutations_observed": 0,
        "source_mutations_observed": 0,
        "home_mutations_observed": 0,
        "env_file_reads_observed": 0,
        "canary_observations": 0,
        "network_commands_observed": 0,
        "npx_commands_observed": 0,
        "codex_marketplace_commands_observed": 0,
        "runtime_drift_counts_changed": False,
        "runtime_drift_claims_added": 0,
        "pairwise_disagreements_added": 0,
    }
    for key, expected in expected_aggregate.items():
        assert_equal(aggregate.get(key), expected, f"aggregate.{key}")

    cases = result.get("cases")
    if not isinstance(cases, list) or len(cases) != 1:
        raise RuntimeError(f"{result_path}: expected one case")
    case = cases[0]
    assert_equal(case.get("case_id"), "project_local_install", "case_id")
    assert_true(case.get("passed"), "case passed")
    assert_false(case.get("dry_run"), "case dry_run")
    assert_equal(case.get("target_changed_files"), [".claude/skills/docs-forge/SKILL.md", "AGENTS.md", "GEMINI.md"], "target_changed_files")
    assert_equal(case.get("unexpected_target_mutations"), [], "unexpected_target_mutations")
    assert_equal(case.get("missing_expected_target_mutations"), [], "missing_expected_target_mutations")
    assert_equal(case.get("file_marker_failures"), {}, "file_marker_failures")
    assert_equal(case.get("source_mutation_count"), 0, "source_mutation_count")
    assert_equal(case.get("home_mutation_count"), 0, "home_mutation_count")
    assert_false(case.get("env_file_read_observed"), "env_file_read_observed")
    assert_equal(case.get("target_canary_hits"), [], "target_canary_hits")
    assert_false(case.get("output_canary_observed"), "output_canary_observed")
    assert_equal(case.get("source_skill_sha256"), case.get("target_skill_sha256"), "skill sha256")
    if case.get("missing_markers"):
        raise RuntimeError(f"{result_path}: case missing markers: {case.get('missing_markers')}")

    sys.path.insert(0, str(REPO_ROOT / "src"))
    from skilldiff.traces import validate_trace_file

    events = validate_trace_file(trace_path)
    event_types = {event["event_type"] for event in events}
    for event_type in {"run.start", "activation.select", "approval.decision", "shell.exec", "filesystem.read", "filesystem.write", "process.exit", "output.generated", "cleanup.observe", "run.end"}:
        if event_type not in event_types:
            raise RuntimeError(f"{trace_path}: missing trace event type {event_type}")
    write_targets = sorted(
        event["target"].removeprefix("./target/")
        for event in events
        if event["event_type"] == "filesystem.write" and str(event.get("target", "")).startswith("./target/")
    )
    assert_equal(write_targets, [".claude/skills/docs-forge/SKILL.md", "AGENTS.md", "GEMINI.md"], "trace filesystem.write targets")

    assert_no_local_paths([result_path, report_path, trace_path])

    print("docs-forge live project-local install verified")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"docs-forge live project-local install validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
