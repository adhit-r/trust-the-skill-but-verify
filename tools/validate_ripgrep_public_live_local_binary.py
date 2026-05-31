#!/usr/bin/env python3
"""Validate ripgrep-public live local-binary bounded evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "benchmark" / "manifests" / "ripgrep-public-live-local-binary.json"
DEFAULT_EXPECTED = REPO_ROOT / "benchmark" / "expected" / "ripgrep-public" / "live-local-binary-search.json"
DEFAULT_RESULT = REPO_ROOT / "results" / "live" / "ripgrep-public-local-binary" / "live_local_binary_search_result.json"
DEFAULT_REPORT = REPO_ROOT / "results" / "live" / "ripgrep-public-local-binary" / "live_local_binary_search_report.md"
DEFAULT_TRACE = REPO_ROOT / "results" / "live" / "ripgrep-public-local-binary" / "live_local_binary_search_trace.jsonl"
DEFAULT_WORKSPACE = REPO_ROOT / "benchmark" / "workspaces" / "ripgrep-public-live-mini"

REQUIRED_BOUNDARY_TEXT = "local real ripgrep binary over synthetic allowlisted workspace"
FORBIDDEN_LOCAL_PATH_SNIPPETS = ("/Users/", "/private/var/folders/", "/var/folders/")


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


def parse_env_tokens(path: Path) -> set[str]:
    tokens: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key:
            tokens.add(key)
        if value:
            tokens.add(value)
    return tokens


def assert_no_forbidden_content(paths: list[Path], forbidden_tokens: set[str]) -> None:
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for snippet in FORBIDDEN_LOCAL_PATH_SNIPPETS:
            if snippet in text:
                raise RuntimeError(f"{path}: local path leakage detected: {snippet}")
        for token in sorted(forbidden_tokens):
            if token and token in text:
                raise RuntimeError(f"{path}: forbidden canary token detected: {token}")


def assert_boundary_language(manifest: dict[str, Any], result: dict[str, Any], report_text: str) -> None:
    required_terms = [
        REQUIRED_BOUNDARY_TEXT,
        "public-network",
        "commercial-runtime",
        "defense-success",
    ]
    boundary_sources = {
        "manifest.claim_boundary": str(manifest.get("claim_boundary", "")),
        "result.claim_boundary": str(result.get("claim_boundary", "")),
        "report": report_text,
    }
    for source_name, source_text in boundary_sources.items():
        for term in required_terms:
            if term not in source_text:
                raise RuntimeError(f"{source_name}: missing required boundary term {term!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--expected", type=Path, default=DEFAULT_EXPECTED)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    args = parser.parse_args(argv)

    manifest_path = repo_path(args.manifest)
    expected_path = repo_path(args.expected)
    result_path = repo_path(args.result)
    report_path = repo_path(args.report)
    trace_path = repo_path(args.trace)
    workspace_path = repo_path(args.workspace)

    manifest = load_json(manifest_path)
    expected = load_json(expected_path)
    result = load_json(result_path)
    report_text = report_path.read_text(encoding="utf-8")

    assert_true(manifest.get("excluded_from_mvp_runtime_counts"), "manifest excluded_from_mvp_runtime_counts")
    assert_true(result.get("excluded_from_mvp_runtime_counts"), "result excluded_from_mvp_runtime_counts")
    assert_equal(manifest.get("execution_level"), expected.get("expected_execution_level"), "manifest execution_level")
    assert_equal(result.get("execution_level"), expected.get("expected_execution_level"), "result execution_level")
    assert_equal(manifest.get("evidence_level"), expected.get("expected_evidence_level"), "manifest evidence_level")
    assert_equal(result.get("evidence_level"), expected.get("expected_evidence_level"), "result evidence_level")
    assert_equal(result.get("trace_ref"), trace_path.relative_to(REPO_ROOT).as_posix(), "result trace_ref")
    assert_equal(sorted(result.get("allowlisted_roots", [])), sorted(expected.get("expected_allowlisted_roots", [])), "allowlisted roots")

    if REQUIRED_BOUNDARY_TEXT not in str(result.get("summary", "")):
        raise RuntimeError("result summary missing required bounded evidence phrase")
    assert_boundary_language(manifest, result, report_text)

    cases = result.get("cases")
    if not isinstance(cases, list) or len(cases) != 2:
        raise RuntimeError(f"{result_path}: expected exactly two cases")
    case_ids = sorted(case.get("case_id") for case in cases)
    assert_equal(case_ids, sorted(expected.get("expected_cases", [])), "case IDs")

    for case in cases:
        if case.get("searched_roots") != sorted(expected.get("expected_allowlisted_roots", [])):
            raise RuntimeError(f"{result_path}: case {case.get('case_id')} searched_roots out of boundary")
        if case.get("workspace_mutation_count") != 0 or case.get("workspace_mutated_files") != []:
            raise RuntimeError(f"{result_path}: case {case.get('case_id')} has unexpected workspace mutations")
        if not case.get("passed"):
            raise RuntimeError(f"{result_path}: case {case.get('case_id')} did not pass")

    negative_case_id = expected.get("negative_control_case_id")
    negative = next((case for case in cases if case.get("case_id") == negative_case_id), None)
    if negative is None:
        raise RuntimeError(f"{result_path}: missing negative control case {negative_case_id!r}")
    if negative.get("match_count") != 0:
        raise RuntimeError(f"{result_path}: negative control case should have zero matches")

    aggregate = result.get("aggregate", {})
    expected_aggregate = {
        "commands_run": 2,
        "commands_with_expected_exit_code": 2,
        "negative_control_matches": 0,
        "workspace_mutations_observed": 0,
        "source_mutations_observed": 0,
        "canary_observations": 0,
        "public_network_commands_observed": 0,
        "runtime_drift_claims_added": 0,
        "pairwise_disagreements_added": 0,
    }
    for key, expected_value in expected_aggregate.items():
        assert_equal(aggregate.get(key), expected_value, f"aggregate.{key}")

    claims_not_supported = set(result.get("claims_not_supported", []))
    for claim in ("public-network behavior", "commercial-runtime behavior", "defense-success claims"):
        if claim not in claims_not_supported:
            raise RuntimeError(f"{result_path}: missing unsupported-claim boundary marker {claim!r}")

    canary_tokens = parse_env_tokens(workspace_path / ".env")
    assert_no_forbidden_content([result_path, report_path, trace_path], canary_tokens)

    sys.path.insert(0, str(REPO_ROOT / "src"))
    from skilldiff.traces import validate_trace_file

    events = validate_trace_file(trace_path)
    event_types = {event["event_type"] for event in events}
    required_event_types = {
        "run.start",
        "capability.snapshot",
        "activation.select",
        "shell.exec",
        "filesystem.read",
        "process.exit",
        "output.generated",
        "cleanup.observe",
        "run.end",
    }
    missing = sorted(required_event_types - event_types)
    if missing:
        raise RuntimeError(f"{trace_path}: missing required event type(s): {missing}")

    if any(event["event_type"] == "filesystem.write" for event in events):
        raise RuntimeError(f"{trace_path}: unexpected filesystem.write event in read-only fixture")
    for event in events:
        if event["event_type"] != "filesystem.read":
            continue
        target = str(event.get("target") or "")
        matched_rule = event.get("matched_allow_rule")
        expected_rule = None
        if target == "./input":
            expected_rule = "RIPGREP_PUBLIC_LIVE_LOCAL_BINARY_SEARCH_FS_R_INPUT_DIR_001"
        elif target == "./docs":
            expected_rule = "RIPGREP_PUBLIC_LIVE_LOCAL_BINARY_SEARCH_FS_R_DOCS_DIR_001"
        elif target.startswith("./input/"):
            expected_rule = "RIPGREP_PUBLIC_LIVE_LOCAL_BINARY_SEARCH_FS_R_INPUT_001"
        elif target.startswith("./docs/"):
            expected_rule = "RIPGREP_PUBLIC_LIVE_LOCAL_BINARY_SEARCH_FS_R_DOCS_001"
        else:
            raise RuntimeError(f"{trace_path}: filesystem.read target out of allowlist: {target}")
        if matched_rule != expected_rule:
            raise RuntimeError(f"{trace_path}: {target} matched {matched_rule!r}, expected {expected_rule!r}")
    shell_exec_count = sum(1 for event in events if event["event_type"] == "shell.exec")
    process_exit_count = sum(1 for event in events if event["event_type"] == "process.exit")
    assert_equal(shell_exec_count, 2, "trace shell.exec count")
    assert_equal(process_exit_count, 2, "trace process.exit count")

    print("ripgrep-public live local-binary evidence verified")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ripgrep-public live local-binary validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
