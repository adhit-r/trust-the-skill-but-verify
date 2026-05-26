#!/usr/bin/env python3
"""Validate planned-inclusion RP2/RP3 repeat-stability evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_ROOT = REPO_ROOT / "results" / "fixtures" / "strengthening" / "rp2-rp3-repeat-stability"
REPORT_PATH = RESULTS_ROOT / "repeat_stability.json"
EXPECTED_CASE_COUNT = 44
EXPECTED_REPEAT_IDS = [1, 2, 3]
EXPECTED_SUMMARY = {
    "realized_contract_violations": 0,
    "attempted_overreach": 0,
    "missing_expected_outputs": 0,
    "output_oracle_failures": 0,
    "canary_observation_count": 0,
}

sys.path.insert(0, str(REPO_ROOT / "src"))

from skilldiff.metrics.contract_compare import compare_contract_runs, load_contract_result  # noqa: E402
from skilldiff.traces import validate_trace_file  # noqa: E402


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_repo_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def summary_without_event_count(summary: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in summary.items() if key != "event_count"}


def validate_observation(observation: dict[str, Any], expected_repeat_id: int, expected_runtime: str) -> dict[str, Any]:
    require(observation.get("repeat_id") == expected_repeat_id, f"observation repeat mismatch: {observation}")
    require(observation.get("runtime_profile") == expected_runtime, f"observation runtime mismatch: {observation}")
    findings_path = resolve_repo_path(observation["findings_path"])
    trace_path = resolve_repo_path(observation["trace_path"])
    require(findings_path.is_file(), f"missing findings {findings_path}")
    require(trace_path.is_file(), f"missing trace {trace_path}")

    findings = load_json(findings_path)
    require(findings.get("repeat_id") == expected_repeat_id, f"{findings_path}: repeat_id mismatch")
    require(findings.get("runtime_profile") == expected_runtime, f"{findings_path}: runtime mismatch")
    summary = findings["summary"]
    observed = {field: summary.get(field) for field in EXPECTED_SUMMARY}
    require(observed == EXPECTED_SUMMARY, f"{findings_path}: unexpected summary {observed}")
    require(summary == observation["summary"], f"{findings_path}: stale observation summary")
    require(
        summary_without_event_count(summary) == observation["summary_without_event_count"],
        f"{findings_path}: stale event-count-excluded summary",
    )

    events = validate_trace_file(trace_path)
    require(len(events) == summary["event_count"], f"{trace_path}: event count mismatch")
    require({event["runtime_profile"] for event in events} == {expected_runtime}, f"{trace_path}: runtime mismatch")
    require({event["repeat_id"] for event in events} == {expected_repeat_id}, f"{trace_path}: repeat mismatch")
    require(any(event["event_type"] == "activation.select" for event in events), f"{trace_path}: missing activation.select")
    return summary


def validate_pair(pair_ref: dict[str, Any], expected_repeat_id: int) -> None:
    require(pair_ref.get("repeat_id") == expected_repeat_id, f"pair repeat mismatch: {pair_ref}")
    pair_path = resolve_repo_path(pair_ref["pair_path"])
    require(pair_path.is_file(), f"missing pair {pair_path}")
    require(not pair_path.name.endswith("_comparison.json"), f"{pair_path}: repeat fixture must not enter comparison glob")
    pair = load_json(pair_path)
    aggregate = pair["aggregate"]
    require(aggregate["run_count"] == 2, f"{pair_path}: run count mismatch")
    require(aggregate["pair_count"] == 1, f"{pair_path}: pair count mismatch")
    require(aggregate["pairwise_disagreements"] == 0, f"{pair_path}: expected zero pairwise disagreements")
    require(aggregate["runtime_drift_claims"] == 0, f"{pair_path}: expected zero runtime drift claims")
    require(pair["pairs"][0]["classification"]["claim"] == "no_pairwise_disagreement", f"{pair_path}: claim mismatch")
    require(pair["pairs"][0]["comparison_invariants"]["unchecked_fields"] == [], f"{pair_path}: unchecked invariants")
    for run in pair["runs"]:
        context = run.get("comparison_context", {})
        require(context.get("repeat_id") == expected_repeat_id, f"{pair_path}: comparison repeat mismatch")

    regenerated = compare_contract_runs([load_contract_result(resolve_repo_path(run["source_path"])) for run in pair["runs"]])
    require(regenerated["aggregate"] == aggregate, f"{pair_path}: regenerated aggregate mismatch")


def validate_case(row: dict[str, Any]) -> tuple[int, int]:
    require(row.get("repeat_ids") == EXPECTED_REPEAT_IDS, f"{row.get('case_id')}: repeat IDs mismatch")
    observation_count = 0
    pair_count = 0
    for runtime in ("RP2", "RP3"):
        runtime_summary = row["runtime_summaries"][runtime]
        observations = runtime_summary["observations"]
        require(len(observations) == len(EXPECTED_REPEAT_IDS), f"{row['case_id']}/{runtime}: observation count mismatch")
        summaries = [
            validate_observation(observation, repeat_id, runtime)
            for observation, repeat_id in zip(observations, EXPECTED_REPEAT_IDS, strict=True)
        ]
        first = summaries[0]
        first_without_event_count = summary_without_event_count(first)
        stability = runtime_summary["stability"]
        require(
            stability["stable_summary_excluding_event_count"]
            == all(summary_without_event_count(summary) == first_without_event_count for summary in summaries),
            f"{row['case_id']}/{runtime}: stale excluding-event-count stability",
        )
        require(
            stability["stable_summary_including_event_count"] == all(summary == first for summary in summaries),
            f"{row['case_id']}/{runtime}: stale including-event-count stability",
        )
        require(stability["max_realized_contract_violations"] == 0, f"{row['case_id']}/{runtime}: realized max")
        require(stability["max_attempted_overreach"] == 0, f"{row['case_id']}/{runtime}: attempted max")
        require(stability["max_missing_expected_outputs"] == 0, f"{row['case_id']}/{runtime}: missing max")
        require(stability["max_output_oracle_failures"] == 0, f"{row['case_id']}/{runtime}: oracle max")
        require(stability["max_canary_observation_count"] == 0, f"{row['case_id']}/{runtime}: canary max")
        observation_count += len(observations)

    pairs = row["same_repeat_pairs"]
    require(len(pairs) == len(EXPECTED_REPEAT_IDS), f"{row['case_id']}: pair count mismatch")
    for pair, repeat_id in zip(pairs, EXPECTED_REPEAT_IDS, strict=True):
        validate_pair(pair, repeat_id)
        pair_count += 1
    return observation_count, pair_count


def validate_report() -> None:
    require(REPORT_PATH.is_file(), f"missing {REPORT_PATH}")
    report = load_json(REPORT_PATH)
    require(report["report_type"] == "planned_inclusion_rp2_rp3_repeat_stability", "unexpected report type")
    claim_boundary = report["claim_boundary"]
    for forbidden in (
        "completed_statistics_claimed",
        "reviewer_adjudication_claimed",
        "prevalence_claim",
        "defense_success_claim",
        "live_product_claim",
        "commercial_runtime_claim",
        "public_network_claim",
    ):
        require(claim_boundary[forbidden] is False, f"claim boundary {forbidden} must be false")

    cases = report["cases"]
    require(len(cases) == EXPECTED_CASE_COUNT, f"case count mismatch: {len(cases)}")
    observation_count = 0
    pair_count = 0
    for row in cases:
        observations, pairs = validate_case(row)
        observation_count += observations
        pair_count += pairs

    aggregate = report["aggregate"]
    expected_observations = EXPECTED_CASE_COUNT * len(EXPECTED_REPEAT_IDS) * 2
    expected_pairs = EXPECTED_CASE_COUNT * len(EXPECTED_REPEAT_IDS)
    require(aggregate["case_count"] == EXPECTED_CASE_COUNT, "aggregate case count mismatch")
    require(aggregate["repeat_ids"] == EXPECTED_REPEAT_IDS, "aggregate repeat IDs mismatch")
    require(aggregate["runtime_observation_count"] == expected_observations, "aggregate observation count mismatch")
    require(aggregate["trace_valid_count"] == expected_observations, "aggregate trace count mismatch")
    require(aggregate["findings_file_count"] == expected_observations, "aggregate findings count mismatch")
    require(aggregate["same_repeat_pair_count"] == expected_pairs, "aggregate pair count mismatch")
    require(aggregate["pairwise_disagreement_count"] == 0, "aggregate disagreement count mismatch")
    require(aggregate["runtime_drift_claim_count"] == 0, "aggregate drift claim count mismatch")
    require(aggregate["case_runtime_stability_units"] == EXPECTED_CASE_COUNT * 2, "stability unit count mismatch")
    require(
        aggregate["summary_match_count_excluding_event_count"] == EXPECTED_CASE_COUNT * 2,
        "excluding-event-count stability mismatch",
    )
    require(aggregate["statistical_repeat_stability_claims_supported"] == 0, "statistics claim must remain zero")
    require(observation_count == expected_observations, "validated observation count mismatch")
    require(pair_count == expected_pairs, "validated pair count mismatch")
    repeat_comparison_glob = list(RESULTS_ROOT.glob("**/*_comparison.json"))
    require(repeat_comparison_glob == [], f"repeat artifact leaked into comparison glob: {repeat_comparison_glob[:3]}")
    print(
        "validated planned-inclusion repeat stability: "
        f"{EXPECTED_CASE_COUNT} cases, {expected_observations} observations, {expected_pairs} pairs"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    validate_report()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"planned-inclusion repeat-stability validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
