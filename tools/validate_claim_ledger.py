#!/usr/bin/env python3
"""Validate paper claim ledger evidence references."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = REPO_ROOT / "paper" / "claim-ledger.json"
sys.path.insert(0, str(REPO_ROOT / "src"))

from skilldiff.metrics.contract_compare import compare_contract_runs, load_contract_result  # noqa: E402


def resolve_pointer(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise ValueError(f"JSON pointer must start with '/': {pointer}")
    value = document
    for raw_part in pointer.lstrip("/").split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            value = value[int(part)]
        elif isinstance(value, dict):
            value = value[part]
        else:
            raise TypeError(f"cannot descend into {type(value).__name__} at {part!r}")
    return value


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_repo_path(value: str) -> Path:
    placeholder = "<REPO_ROOT>/"
    if value.startswith(placeholder):
        return REPO_ROOT / value.removeprefix(placeholder)
    path = Path(value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def evidence_path(evidence: dict[str, Any]) -> Path:
    path = evidence.get("path")
    if not isinstance(path, str) or not path:
        raise ValueError("evidence path is required")
    return REPO_ROOT / path


def expect_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, observed {actual!r}")


def glob_matches(pattern: str, exclude_globs: list[str] | None = None) -> list[Path]:
    files = sorted(REPO_ROOT.glob(pattern))
    excluded: set[Path] = set()
    for exclude_glob in exclude_globs or []:
        excluded.update(REPO_ROOT.glob(exclude_glob))
    if excluded:
        files = [path for path in files if path not in excluded]
    return files


def evidence_exclude_globs(evidence: dict[str, Any]) -> list[str] | None:
    exclude_globs = evidence.get("exclude_globs")
    if exclude_globs is None:
        return None
    if not isinstance(exclude_globs, list) or not all(isinstance(item, str) for item in exclude_globs):
        raise ValueError("exclude_globs must be a list of strings")
    return exclude_globs


def comparison_files(pattern: str, exclude_globs: list[str] | None = None) -> list[Path]:
    files = glob_matches(pattern, exclude_globs)
    if not files:
        raise FileNotFoundError(f"no comparison files matched {pattern!r}")
    return files


def git_tracked_files(pattern: str) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "--", pattern],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"git ls-files failed for {pattern!r}: {completed.stderr.strip()}")
    return sorted(line for line in completed.stdout.splitlines() if line.strip())


def nonblank_line_count(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def validate_comparison_file(path: Path) -> dict[str, Any]:
    comparison = load_json(path)
    pairs = comparison.get("pairs")
    runs = comparison.get("runs")
    aggregate = comparison.get("aggregate")
    if not isinstance(pairs, list) or not isinstance(runs, list) or not isinstance(aggregate, dict):
        raise ValueError(f"{path}: comparison must contain aggregate, runs, and pairs")

    expect_equal(
        aggregate.get("pairwise_disagreements"),
        sum(pair.get("disagreement_count", 0) for pair in pairs),
        f"{path}: aggregate.pairwise_disagreements",
    )
    expect_equal(
        aggregate.get("runtime_drift_claims"),
        sum(1 for pair in pairs if pair.get("classification", {}).get("claim") == "runtime_drift_candidate"),
        f"{path}: aggregate.runtime_drift_claims",
    )

    source_paths: list[Path] = []
    for pair in pairs:
        invariants = pair.get("comparison_invariants", {})
        strict_mismatches = invariants.get("strict_mismatches", [])
        if pair.get("classification", {}).get("claim") == "runtime_drift_candidate" and strict_mismatches:
            raise AssertionError(f"{path}: runtime drift candidate has strict mismatches: {strict_mismatches}")

    for run in runs:
        source_path = resolve_repo_path(run["source_path"])
        trace_path = resolve_repo_path(run["trace_path"])
        if not source_path.is_file():
            raise FileNotFoundError(f"{path}: missing run source_path {source_path}")
        if not trace_path.is_file():
            raise FileNotFoundError(f"{path}: missing run trace_path {trace_path}")
        source_paths.append(source_path)

        findings = load_json(source_path)
        if findings.get("summary", {}).get("trace_valid") is not True:
            raise AssertionError(f"{source_path}: summary.trace_valid is not true")
        expect_equal(
            findings.get("summary", {}).get("event_count"),
            nonblank_line_count(trace_path),
            f"{source_path}: summary.event_count",
        )

    regenerated = compare_contract_runs([load_contract_result(path) for path in source_paths])
    expect_equal(
        regenerated.get("aggregate"),
        aggregate,
        f"{path}: regenerated aggregate",
    )
    return comparison


def validate_no_unchecked_comparison_fields(path: Path) -> None:
    comparison = validate_comparison_file(path)
    runs = comparison.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError(f"{path}: comparison_no_unchecked_fields requires non-empty runs")
    for run in runs:
        context = run.get("comparison_context")
        if not isinstance(context, dict):
            raise AssertionError(f"{path}: run {run.get('run_id')} missing comparison_context")
        missing_fields = context.get("missing_invariant_fields", [])
        if not isinstance(missing_fields, list):
            raise AssertionError(f"{path}: run {run.get('run_id')} has invalid missing_invariant_fields")
        if missing_fields:
            raise AssertionError(f"{path}: run {run.get('run_id')} missing invariant fields: {missing_fields}")

    pairs = comparison.get("pairs")
    if not isinstance(pairs, list) or not pairs:
        raise ValueError(f"{path}: comparison_no_unchecked_fields requires non-empty pairs")
    for index, pair in enumerate(pairs):
        invariants = pair.get("comparison_invariants")
        if not isinstance(invariants, dict):
            raise AssertionError(f"{path}: pair {index} missing comparison_invariants")
        unchecked_fields = invariants.get("unchecked_fields", [])
        if not isinstance(unchecked_fields, list):
            raise AssertionError(f"{path}: pair {index} has invalid unchecked_fields")
        if unchecked_fields:
            raise AssertionError(f"{path}: pair {index} has unchecked invariant fields: {unchecked_fields}")


def validate_evidence(evidence: dict[str, Any]) -> None:
    evidence_type = evidence.get("type")
    if evidence_type == "file_contains":
        path = evidence_path(evidence)
        contains = evidence.get("contains")
        if not isinstance(contains, str) or not contains:
            raise ValueError(f"{path}: file_contains evidence requires contains")
        text = path.read_text(encoding="utf-8")
        if contains not in text:
            raise AssertionError(f"{path}: missing required text {contains!r}")
        return

    if evidence_type == "glob_count":
        pattern = evidence.get("glob")
        if not isinstance(pattern, str) or not pattern:
            raise ValueError("glob_count evidence requires glob")
        matches = glob_matches(pattern, evidence_exclude_globs(evidence))
        expect_equal(len(matches), evidence.get("expected"), pattern)
        return

    if evidence_type == "git_tracked_glob_count":
        pattern = evidence.get("glob")
        if not isinstance(pattern, str) or not pattern:
            raise ValueError("git_tracked_glob_count evidence requires glob")
        matches = git_tracked_files(pattern)
        expect_equal(len(matches), evidence.get("expected"), f"git ls-files {pattern}")
        return

    if evidence_type == "comparison_aggregate_sum":
        pattern = evidence.get("glob")
        field = evidence.get("field")
        if not isinstance(pattern, str) or not isinstance(field, str):
            raise ValueError("comparison_aggregate_sum evidence requires glob and field")
        files = comparison_files(pattern, evidence_exclude_globs(evidence))
        if "expected_source_count" in evidence:
            expect_equal(len(files), evidence["expected_source_count"], f"{pattern}: source count")
        total = sum(validate_comparison_file(path).get("aggregate", {}).get(field, 0) for path in files)
        expect_equal(total, evidence.get("expected"), f"{pattern}: aggregate.{field} sum")
        return

    if evidence_type == "comparison_unique_trace_count":
        pattern = evidence.get("glob")
        if not isinstance(pattern, str):
            raise ValueError("comparison_unique_trace_count evidence requires glob")
        files = comparison_files(pattern, evidence_exclude_globs(evidence))
        if "expected_source_count" in evidence:
            expect_equal(len(files), evidence["expected_source_count"], f"{pattern}: source count")
        trace_paths = {
            resolve_repo_path(run["trace_path"]).relative_to(REPO_ROOT).as_posix()
            for path in files
            for run in validate_comparison_file(path).get("runs", [])
        }
        expect_equal(len(trace_paths), evidence.get("expected"), f"{pattern}: unique trace count")
        return

    if evidence_type == "comparison_no_unchecked_fields":
        pattern = evidence.get("glob")
        if not isinstance(pattern, str):
            raise ValueError("comparison_no_unchecked_fields evidence requires glob")
        files = comparison_files(pattern, evidence_exclude_globs(evidence))
        if "expected_source_count" in evidence:
            expect_equal(len(files), evidence["expected_source_count"], f"{pattern}: source count")
        for path in files:
            validate_no_unchecked_comparison_fields(path)
        return

    path = evidence_path(evidence)
    document = load_json(path)

    if evidence_type == "json_value":
        actual = resolve_pointer(document, evidence["pointer"])
        expect_equal(actual, evidence.get("expected"), f"{path}:{evidence['pointer']}")
        return

    if evidence_type == "json_len":
        actual = len(resolve_pointer(document, evidence["pointer"]))
        expect_equal(actual, evidence.get("expected"), f"{path}:{evidence['pointer']} length")
        return

    if evidence_type == "json_sum":
        actual = sum(resolve_pointer(document, pointer) for pointer in evidence["pointers"])
        expect_equal(actual, evidence.get("expected"), f"{path}:sum")
        return

    if evidence_type == "json_object_key_count_sum":
        actual = sum(len(resolve_pointer(document, pointer)) for pointer in evidence["pointers"])
        expect_equal(actual, evidence.get("expected"), f"{path}:object-key-count-sum")
        return

    if evidence_type == "json_object_key_count_min":
        target = resolve_pointer(document, evidence["pointer"])
        if not isinstance(target, dict):
            raise AssertionError(
                f"{path}:{evidence['pointer']} must resolve to a JSON object"
            )
        actual = len(target)
        minimum = evidence.get("minimum")
        if not isinstance(minimum, int):
            raise ValueError(
                f"{path}: json_object_key_count_min requires integer minimum"
            )
        if actual < minimum:
            raise AssertionError(
                f"{path}:{evidence['pointer']} key count: expected at least "
                f"{minimum}, observed {actual}"
            )
        return

    raise ValueError(f"unsupported evidence type: {evidence_type}")


def validate_ledger(path: Path) -> int:
    ledger = load_json(path)
    claims = ledger.get("claims")
    if not isinstance(claims, list) or not claims:
        raise ValueError(f"{path}: claims must be a non-empty list")

    seen_ids: set[str] = set()
    evidence_count = 0
    for claim in claims:
        claim_id = claim.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id:
            raise ValueError(f"{path}: every claim needs claim_id")
        if claim_id in seen_ids:
            raise ValueError(f"{path}: duplicate claim_id {claim_id}")
        seen_ids.add(claim_id)

        for paper_path in claim.get("paper_locations", []):
            location_path = REPO_ROOT / paper_path
            if not location_path.exists():
                raise FileNotFoundError(f"{claim_id}: paper location missing: {paper_path}")

        evidence_items = claim.get("evidence")
        if not isinstance(evidence_items, list) or not evidence_items:
            raise ValueError(f"{claim_id}: evidence must be a non-empty list")
        for evidence in evidence_items:
            validate_evidence(evidence)
            evidence_count += 1

    print(f"validated {len(claims)} claim(s), {evidence_count} evidence reference(s)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    args = parser.parse_args(argv)
    ledger_path = args.ledger if args.ledger.is_absolute() else REPO_ROOT / args.ledger
    return validate_ledger(ledger_path)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"claim ledger validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
