#!/usr/bin/env python3
"""Validate source-only external-validity scaffold boundaries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "benchmark" / "manifests" / "external-validity-scaffolds.json"
DEFAULT_RESULT = REPO_ROOT / "results" / "external" / "first-party-source-provenance.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_ref_path(ref: str) -> Path:
    path_text = ref.split("#", 1)[0]
    if not path_text:
        raise ValueError(f"invalid ref: {ref}")
    return REPO_ROOT / path_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    args = parser.parse_args(argv)

    manifest_path = args.manifest if args.manifest.is_absolute() else REPO_ROOT / args.manifest
    result_path = args.result if args.result.is_absolute() else REPO_ROOT / args.result

    manifest = load_json(manifest_path)
    result = load_json(result_path)
    prohibited = set(manifest.get("prohibited_scaffold_fields", []))
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        raise RuntimeError(f"{manifest_path}: entries must be a non-empty list")

    if manifest.get("excluded_from_mvp_runtime_counts") is not True:
        raise RuntimeError(f"{manifest_path}: manifest must be excluded from MVP runtime counts")

    for entry in entries:
        if not isinstance(entry, dict):
            raise RuntimeError(f"{manifest_path}: entries must be objects")
        overlap = prohibited.intersection(entry)
        if overlap:
            raise RuntimeError(
                f"{manifest_path}: scaffold {entry.get('case_id')} contains prohibited result fields: {sorted(overlap)}"
            )
        if entry.get("execution_level") != "source_provenance_only":
            raise RuntimeError(f"{manifest_path}: scaffold {entry.get('case_id')} must be source_provenance_only")
        if entry.get("excluded_from_mvp_runtime_counts") is not True:
            raise RuntimeError(f"{manifest_path}: scaffold {entry.get('case_id')} must be excluded from MVP counts")
        for ref_key in ("controlled_fixture_manifest_ref", "source_provenance_result_ref"):
            ref = entry.get(ref_key)
            if not isinstance(ref, str) or not ref:
                raise RuntimeError(f"{manifest_path}: scaffold {entry.get('case_id')} missing {ref_key}")
            if not resolve_ref_path(ref).is_file():
                raise FileNotFoundError(f"{manifest_path}: missing {ref_key} target {ref}")

    aggregate = result.get("aggregate", {})
    expected_values = {
        "repositories_checked": 2,
        "repositories_verified": 2,
        "pinned_source_hashes_verified": 53,
        "workspace_fixtures_verified": 2,
        "full_product_workloads_executed": 0,
        "full_source_trees_vendored": 0,
    }
    for key, expected in expected_values.items():
        observed = aggregate.get(key)
        if observed != expected:
            raise RuntimeError(f"{result_path}: aggregate.{key} expected {expected}, observed {observed}")
    if aggregate.get("real_secrets_present") is not False:
        raise RuntimeError(f"{result_path}: aggregate.real_secrets_present must be false")

    cases = result.get("cases")
    if not isinstance(cases, list) or len(cases) != len(entries):
        raise RuntimeError(f"{result_path}: cases must align with scaffold entries")
    for case in cases:
        if case.get("verification_status") != "passed":
            raise RuntimeError(f"{result_path}: case {case.get('case_id')} did not pass")
        if case.get("full_product_workload_executed") is not False:
            raise RuntimeError(f"{result_path}: case {case.get('case_id')} must not execute full product workloads")
        if case.get("pinned_source_hashes_verified") is not True:
            raise RuntimeError(f"{result_path}: case {case.get('case_id')} did not verify pinned source hashes")

    print(f"external-validity scaffolds verified: {len(entries)} source-only entries")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"external-validity scaffold validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
