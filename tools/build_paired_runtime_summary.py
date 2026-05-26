#!/usr/bin/env python3
"""Build a bounded paired-runtime summary from existing comparison artifacts."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "results" / "derived" / "paired-runtime-summary.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def comparison_files() -> list[Path]:
    return sorted(
        path
        for path in REPO_ROOT.glob("results/**/*.json")
        if path.name.endswith("_comparison.json")
    )


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def source_summary(run: dict[str, Any]) -> dict[str, Any]:
    source_path = REPO_ROOT / run["source_path"]
    if not source_path.is_file():
        return run.get("summary", {})
    source = load_json(source_path)
    summary = source.get("summary")
    return summary if isinstance(summary, dict) else run.get("summary", {})


def context_key(context: dict[str, Any]) -> str:
    return "|".join(
        [
            str(context.get("skill_id") or "unknown-skill"),
            str(context.get("task_id") or "unknown-task"),
            str(context.get("contract_id") or "unknown-contract"),
            str(context.get("variant_id") or "unknown-variant"),
            f"repeat:{context.get('repeat_id', 'unknown')}",
        ]
    )


def summarize_pair(
    comparison_path: Path,
    pair: dict[str, Any],
    runs_by_id: dict[str, dict[str, Any]],
    group: dict[str, Any],
) -> None:
    left = runs_by_id[pair["left_run_id"]]
    right = runs_by_id[pair["right_run_id"]]
    left_summary = source_summary(left)
    right_summary = source_summary(right)
    claim = pair.get("classification", {}).get("claim") or "unknown"
    runtime_pair = f"{pair['left_runtime_profile']}__{pair['right_runtime_profile']}"

    group["source_comparisons"].add(rel(comparison_path))
    group["runtime_pairs"][runtime_pair] += 1
    group["pair_count"] += 1
    group["pairwise_disagreements"] += int(pair.get("disagreement_count", 0))
    group["classification_counts"][claim] += 1
    group["runtime_profiles"].update([pair["left_runtime_profile"], pair["right_runtime_profile"]])
    group["run_ids"].update([pair["left_run_id"], pair["right_run_id"]])
    group["trace_paths"].update([left["trace_path"], right["trace_path"]])

    if claim == "runtime_drift_candidate":
        group["runtime_drift_candidate_pairs"] += 1
    if claim == "mitigation_report_card_comparison":
        group["mitigation_report_card_pairs"] += 1

    for summary in (left_summary, right_summary):
        group["realized_contract_violations"] += int(summary.get("realized_contract_violations", 0))
        group["attempted_overreach"] += int(summary.get("attempted_overreach", 0))
        group["missing_expected_outputs"] += int(summary.get("missing_expected_outputs", 0))
        group["output_oracle_failures"] += int(summary.get("output_oracle_failures", 0))
        group["canary_observation_count"] += int(summary.get("canary_observation_count", 0))


def empty_group(group_key: str, context: dict[str, Any]) -> dict[str, Any]:
    return {
        "group_key": group_key,
        "skill_id": context.get("skill_id") or "unknown",
        "task_id": context.get("task_id") or "unknown",
        "contract_id": context.get("contract_id") or "unknown",
        "variant_id": context.get("variant_id") or "unknown",
        "repeat_id": context.get("repeat_id"),
        "source_comparisons": set(),
        "runtime_profiles": set(),
        "runtime_pairs": Counter(),
        "run_ids": set(),
        "trace_paths": set(),
        "pair_count": 0,
        "pairwise_disagreements": 0,
        "runtime_drift_candidate_pairs": 0,
        "mitigation_report_card_pairs": 0,
        "classification_counts": Counter(),
        "realized_contract_violations": 0,
        "attempted_overreach": 0,
        "missing_expected_outputs": 0,
        "output_oracle_failures": 0,
        "canary_observation_count": 0,
    }


def finalize_group(group: dict[str, Any]) -> dict[str, Any]:
    return {
        **{
            key: value
            for key, value in group.items()
            if key
            not in {
                "source_comparisons",
                "runtime_profiles",
                "runtime_pairs",
                "run_ids",
                "trace_paths",
                "classification_counts",
            }
        },
        "source_comparisons": sorted(group["source_comparisons"]),
        "runtime_profiles": sorted(group["runtime_profiles"]),
        "runtime_pairs": dict(sorted(group["runtime_pairs"].items())),
        "classification_counts": dict(sorted(group["classification_counts"].items())),
        "unique_run_count": len(group["run_ids"]),
        "unique_trace_count": len(group["trace_paths"]),
    }


def build_summary() -> dict[str, Any]:
    sources = comparison_files()
    groups: dict[str, dict[str, Any]] = {}
    aggregate_classifications: Counter[str] = Counter()
    aggregate_runtime_pairs: Counter[str] = Counter()
    aggregate_profiles: set[str] = set()
    aggregate_trace_paths: set[str] = set()
    comparison_scope_counts: Counter[str] = Counter()

    run_count = 0
    pair_count = 0
    pairwise_disagreements = 0
    runtime_drift_candidates = 0
    mitigation_pairs = 0

    for comparison_path in sources:
        comparison = load_json(comparison_path)
        runs = comparison.get("runs", [])
        pairs = comparison.get("pairs", [])
        run_count += len(runs)
        pair_count += len(pairs)
        runs_by_id = {run["run_id"]: run for run in runs}
        relative_parts = comparison_path.relative_to(REPO_ROOT).parts
        comparison_scope_counts[relative_parts[1] if len(relative_parts) > 1 else "unknown"] += 1

        for run in runs:
            aggregate_profiles.add(run["runtime_profile"])
            aggregate_trace_paths.add(run["trace_path"])

        for pair in pairs:
            claim = pair.get("classification", {}).get("claim") or "unknown"
            aggregate_classifications[claim] += 1
            aggregate_runtime_pairs[f"{pair['left_runtime_profile']}__{pair['right_runtime_profile']}"] += 1
            pairwise_disagreements += int(pair.get("disagreement_count", 0))
            if claim == "runtime_drift_candidate":
                runtime_drift_candidates += 1
            if claim == "mitigation_report_card_comparison":
                mitigation_pairs += 1

            left_context = runs_by_id[pair["left_run_id"]].get("comparison_context", {})
            key = context_key(left_context)
            group = groups.setdefault(key, empty_group(key, left_context))
            summarize_pair(comparison_path, pair, runs_by_id, group)

    finalized_groups = sorted(
        (finalize_group(group) for group in groups.values()),
        key=lambda item: item["group_key"],
    )

    return {
        "schema_version": "0.1",
        "report_type": "paired_runtime_summary",
        "boundary": (
            "Existing comparison-artifact aggregation layer; not a completed statistical analysis, "
            "not reviewer-adjudication evidence, and not prevalence or defense-success evidence."
        ),
        "claim_boundary": {
            "completed_statistics_claimed": False,
            "reviewer_adjudication_claimed": False,
            "prevalence_claim": False,
            "defense_success_claim": False,
        },
        "aggregate": {
            "comparison_file_count": len(sources),
            "comparison_scope_counts": dict(sorted(comparison_scope_counts.items())),
            "run_count": run_count,
            "pair_count": pair_count,
            "unique_trace_count": len(aggregate_trace_paths),
            "runtime_profiles": sorted(aggregate_profiles),
            "runtime_pair_counts": dict(sorted(aggregate_runtime_pairs.items())),
            "pairwise_disagreement_count": pairwise_disagreements,
            "runtime_drift_candidate_pair_count": runtime_drift_candidates,
            "mitigation_report_card_pair_count": mitigation_pairs,
            "classification_counts": dict(sorted(aggregate_classifications.items())),
            "group_count": len(finalized_groups),
        },
        "groups": finalized_groups,
        "next_statistics_dependencies": [
            "Add repeat coverage for promoted RP2/RP3 cases before Wilson or bootstrap interval claims.",
            "Use this grouped denominator as the input layer for paired runtime summaries.",
            "Keep RP6 mitigation/report-card pairs separate from runtime-drift candidate pairs.",
            "Add manual adjudication records before claiming reviewer agreement or Cohen's kappa.",
        ],
    }


def write_markdown(path: Path, summary: dict[str, Any]) -> None:
    aggregate = summary["aggregate"]
    lines = [
        "# Paired Runtime Summary",
        "",
        summary["boundary"],
        "",
        "## Aggregate",
        "",
        f"- Comparison files: `{aggregate['comparison_file_count']}`",
        f"- Pair count: `{aggregate['pair_count']}`",
        f"- Run count: `{aggregate['run_count']}`",
        f"- Unique traces: `{aggregate['unique_trace_count']}`",
        f"- Pairwise disagreement count: `{aggregate['pairwise_disagreement_count']}`",
        f"- Runtime-drift candidate pairs: `{aggregate['runtime_drift_candidate_pair_count']}`",
        f"- Mitigation/report-card pairs: `{aggregate['mitigation_report_card_pair_count']}`",
        f"- Runtime profiles: `{', '.join(aggregate['runtime_profiles'])}`",
        "",
        "This is an aggregation layer, not Wilson/bootstrap statistics or reviewer agreement evidence.",
        "",
        "## Runtime Pair Counts",
        "",
        "| Runtime Pair | Count |",
        "| --- | ---: |",
    ]
    for runtime_pair, count in aggregate["runtime_pair_counts"].items():
        lines.append(f"| `{runtime_pair}` | {count} |")

    lines.extend(
        [
            "",
            "## Grouped Pair Inputs",
            "",
            "| Skill | Task | Variant | Repeat | Pairs | Disagreements | Drift Candidates | Mitigation Pairs |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for group in summary["groups"]:
        lines.append(
            "| `{skill}` | `{task}` | `{variant}` | {repeat} | {pairs} | {disagreements} | {drift} | {mitigation} |".format(
                skill=group["skill_id"],
                task=group["task_id"],
                variant=group["variant_id"],
                repeat=group["repeat_id"],
                pairs=group["pair_count"],
                disagreements=group["pairwise_disagreements"],
                drift=group["runtime_drift_candidate_pairs"],
                mitigation=group["mitigation_report_card_pairs"],
            )
        )

    lines.extend(["", "## Next Dependencies", ""])
    for item in summary["next_statistics_dependencies"]:
        lines.append(f"- {item}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    output = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    summary = build_summary()
    write_json(output, summary)
    write_markdown(output.with_suffix(".md"), summary)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
