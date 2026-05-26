#!/usr/bin/env python3
"""Validate the derived paired-runtime summary artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY = REPO_ROOT / "results" / "derived" / "paired-runtime-summary.json"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import build_paired_runtime_summary  # noqa: E402


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def comparison_files() -> list[Path]:
    return sorted(
        path
        for path in REPO_ROOT.glob("results/**/*.json")
        if path.name.endswith("_comparison.json")
    )


def validate_summary(path: Path) -> None:
    summary = load_json(path)
    require(summary.get("schema_version") == "0.1", "schema version mismatch")
    require(summary.get("report_type") == "paired_runtime_summary", "report type mismatch")
    boundary = summary.get("boundary", "")
    require("not a completed statistical analysis" in boundary, "boundary must exclude completed statistics")
    require("not reviewer-adjudication evidence" in boundary, "boundary must exclude reviewer adjudication")

    sources = comparison_files()
    recomputed = build_paired_runtime_summary.build_summary()
    require(summary == recomputed, "paired-runtime summary is stale")

    aggregate = summary.get("aggregate", {})
    require(aggregate.get("comparison_file_count") == len(sources), "comparison file count mismatch")
    require(aggregate.get("comparison_file_count", 0) > 0, "expected at least one comparison file")

    observed_pair_count = 0
    observed_pairwise_disagreements = 0
    observed_runtime_drift_candidates = 0
    observed_mitigation_pairs = 0
    observed_run_count = 0
    observed_trace_paths: set[str] = set()
    observed_runtime_profiles: set[str] = set()
    observed_group_keys: set[str] = set()

    for source in sources:
        comparison = load_json(source)
        pairs = comparison.get("pairs", [])
        runs = comparison.get("runs", [])
        require(isinstance(pairs, list), f"{source}: pairs must be a list")
        require(isinstance(runs, list), f"{source}: runs must be a list")
        observed_pair_count += len(pairs)
        observed_run_count += len(runs)
        for run in runs:
            observed_runtime_profiles.add(run["runtime_profile"])
            observed_trace_paths.add(run["trace_path"])
        for pair in pairs:
            observed_pairwise_disagreements += int(pair.get("disagreement_count", 0))
            claim = pair.get("classification", {}).get("claim")
            if claim == "runtime_drift_candidate":
                observed_runtime_drift_candidates += 1
            if claim == "mitigation_report_card_comparison":
                observed_mitigation_pairs += 1
        for group in summary.get("groups", []):
            for source_ref in group.get("source_comparisons", []):
                if source_ref == source.relative_to(REPO_ROOT).as_posix():
                    observed_group_keys.add(group["group_key"])

    require(aggregate.get("pair_count") == observed_pair_count, "pair count mismatch")
    require(aggregate.get("run_count") == observed_run_count, "run count mismatch")
    require(
        aggregate.get("pairwise_disagreement_count") == observed_pairwise_disagreements,
        "pairwise disagreement count mismatch",
    )
    require(
        aggregate.get("runtime_drift_candidate_pair_count") == observed_runtime_drift_candidates,
        "runtime drift candidate count mismatch",
    )
    require(
        aggregate.get("mitigation_report_card_pair_count") == observed_mitigation_pairs,
        "mitigation pair count mismatch",
    )
    require(
        aggregate.get("unique_trace_count") == len(observed_trace_paths),
        "unique trace count mismatch",
    )
    require(
        sorted(aggregate.get("runtime_profiles", [])) == sorted(observed_runtime_profiles),
        "runtime profile list mismatch",
    )
    require(summary.get("groups"), "expected at least one grouped pair summary")
    require(
        len(observed_group_keys) == len(summary.get("groups", [])),
        "every group must reference at least one source comparison",
    )

    claim_boundary = summary.get("claim_boundary", {})
    for key in (
        "completed_statistics_claimed",
        "reviewer_adjudication_claimed",
        "prevalence_claim",
        "defense_success_claim",
    ):
        require(claim_boundary.get(key) is False, f"claim boundary {key} must be false")

    markdown_path = path.with_suffix(".md")
    require(markdown_path.is_file(), "missing paired-runtime summary Markdown")
    markdown = markdown_path.read_text(encoding="utf-8")
    require(boundary in markdown, "Markdown boundary is stale")
    require(
        f"Comparison files: `{aggregate['comparison_file_count']}`" in markdown,
        "Markdown comparison file count is stale",
    )
    require(
        "This is an aggregation layer, not Wilson/bootstrap statistics or reviewer agreement evidence." in markdown,
        "Markdown claim boundary missing",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args(argv)
    summary_path = args.summary if args.summary.is_absolute() else REPO_ROOT / args.summary
    validate_summary(summary_path)
    print("validated paired-runtime summary")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"paired-runtime summary validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
