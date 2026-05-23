#!/usr/bin/env python3
"""Validate docs-forge live installer dry-run evidence boundaries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "benchmark" / "manifests" / "docs-forge-live-installer.json"
DEFAULT_RESULT = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "dry_run_result.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise RuntimeError(f"{label}: expected {expected!r}, observed {actual!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    args = parser.parse_args(argv)

    manifest_path = repo_path(args.manifest)
    result_path = repo_path(args.result)
    manifest = load_json(manifest_path)
    result = load_json(result_path)

    assert_equal(manifest.get("excluded_from_mvp_runtime_counts"), True, "manifest excluded_from_mvp_runtime_counts")
    assert_equal(result.get("excluded_from_mvp_runtime_counts"), True, "result excluded_from_mvp_runtime_counts")
    assert_equal(manifest.get("execution_level"), "live_node_cli_dry_run", "manifest execution_level")
    assert_equal(result.get("execution_level"), "live_node_cli_dry_run", "result execution_level")
    assert_equal(result.get("safe_to_publish"), True, "result safe_to_publish")
    assert_equal(result.get("real_secrets_present"), False, "result real_secrets_present")

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
        "commands_run": 4,
        "commands_succeeded": 4,
        "dry_run_installer_commands_run": 2,
        "target_mutations_observed": 0,
        "source_mutations_observed": 0,
        "non_dry_run_installs_executed": 0,
        "runtime_drift_counts_changed": False,
        "runtime_drift_claims_added": 0,
        "pairwise_disagreements_added": 0,
    }
    for key, expected in expected_aggregate.items():
        assert_equal(aggregate.get(key), expected, f"aggregate.{key}")

    cases = result.get("cases")
    if not isinstance(cases, list) or len(cases) != 4:
        raise RuntimeError(f"{result_path}: expected four cases")
    dry_run_cases = {"project_agents_dry_run", "codex_dry_run"}
    for case in cases:
        case_id = case.get("case_id")
        if case.get("passed") is not True:
            raise RuntimeError(f"{result_path}: case did not pass: {case_id}")
        if case.get("target_mutation_count") != 0:
            raise RuntimeError(f"{result_path}: case mutated target: {case_id}")
        if case.get("source_status_clean_after") is not True:
            raise RuntimeError(f"{result_path}: source not clean after case: {case_id}")
        if case_id in dry_run_cases and case.get("dry_run") is not True:
            raise RuntimeError(f"{result_path}: installer case is not dry-run: {case_id}")
        if case_id not in dry_run_cases and case.get("dry_run") is not False:
            raise RuntimeError(f"{result_path}: non-installer surface unexpectedly marked dry-run: {case_id}")
        if case.get("missing_markers"):
            raise RuntimeError(f"{result_path}: case missing markers: {case_id}")

    text = result_path.read_text(encoding="utf-8")
    for forbidden in ("/Users/", "/private/var/folders/", "/var/folders/"):
        if forbidden in text:
            raise RuntimeError(f"{result_path}: local path leakage detected: {forbidden}")

    print("docs-forge live installer dry-run verified")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"docs-forge live installer validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
