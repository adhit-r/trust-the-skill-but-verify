#!/usr/bin/env python3
"""Validate current main RP2/RP3 repeat-stability evidence."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "benchmark" / "manifests" / "benchmark-cases-current.json"
RESULTS_ROOT = REPO_ROOT / "results" / "fixtures" / "strengthening" / "rp2-rp3-main-repeat-stability"
REPORT_PATH = RESULTS_ROOT / "repeat_stability.json"
EXECUTION_LEVELS = {
    "controlled_python_fixture_rp2_rp3",
    "controlled_python_fixture_rp2_rp3_negative_control",
    "controlled_python_fixture_rp2_rp3_semantic_event_fixture",
    "controlled_python_fixture_rp2_rp3_local_fake_sink",
}
DEFAULT_REPEAT_IDS = [1, 2, 3]
SUMMARY_FIELDS = {
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


def current_cases() -> list[dict[str, Any]]:
    manifest = load_json(MANIFEST_PATH)
    cases = [
        case
        for case in manifest.get("cases", [])
        if case.get("execution", {}).get("execution_level") in EXECUTION_LEVELS
        and "planned" not in case.get("provenance", {}).get("source_manifest_ref", "")
    ]
    return sorted(cases, key=lambda case: (case["family_id"], case["provenance"]["task_id"]))


def select_cases(all_cases: list[dict[str, Any]], families: list[str], case_ids: list[str]) -> list[dict[str, Any]]:
    cases = all_cases
    if families:
        family_set = set(families)
        cases = [case for case in cases if case["family_id"] in family_set]
    if case_ids:
        case_id_set = set(case_ids)
        cases = [case for case in cases if case["case_id"] in case_id_set]
    return cases


def validate_observation(
    case_id: str,
    observation: dict[str, Any],
    expected_repeat_id: int,
    expected_runtime: str,
) -> dict[str, Any]:
    require(observation.get("repeat_id") == expected_repeat_id, f"{case_id}: observation repeat mismatch: {observation}")
    require(observation.get("runtime_profile") == expected_runtime, f"{case_id}: observation runtime mismatch: {observation}")
    findings_path = resolve_repo_path(observation["findings_path"])
    trace_path = resolve_repo_path(observation["trace_path"])
    require(findings_path.is_file(), f"missing findings {findings_path}")
    require(trace_path.is_file(), f"missing trace {trace_path}")

    findings = load_json(findings_path)
    require(findings.get("repeat_id") == expected_repeat_id, f"{findings_path}: repeat_id mismatch")
    require(findings.get("runtime_profile") == expected_runtime, f"{findings_path}: runtime mismatch")
    summary = findings["summary"]
    for field in SUMMARY_FIELDS:
        require(field in summary, f"{findings_path}: missing summary field {field}")
        require(isinstance(summary[field], int), f"{findings_path}: summary field {field} is not an integer")
        require(summary[field] >= 0, f"{findings_path}: negative summary field {field}")
    require(summary == observation["summary"], f"{findings_path}: stale observation summary")
    require(
        summary_without_event_count(summary) == observation["summary_without_event_count"],
        f"{findings_path}: stale event-count-excluded summary",
    )

    events = validate_trace_file(trace_path)
    require(len(events) == summary["event_count"], f"{trace_path}: event count mismatch")
    require({event["runtime_profile"] for event in events} == {expected_runtime}, f"{trace_path}: runtime mismatch")
    require({event["repeat_id"] for event in events} == {expected_repeat_id}, f"{trace_path}: repeat mismatch")
    return summary


def validate_pair(pair_ref: dict[str, Any], expected_repeat_id: int) -> tuple[int, int, str]:
    require(pair_ref.get("repeat_id") == expected_repeat_id, f"pair repeat mismatch: {pair_ref}")
    pair_path = resolve_repo_path(pair_ref["pair_path"])
    require(pair_path.is_file(), f"missing pair {pair_path}")
    require(not pair_path.name.endswith("_comparison.json"), f"{pair_path}: repeat fixture must not enter comparison glob")
    pair = load_json(pair_path)
    aggregate = pair["aggregate"]
    require(aggregate["run_count"] == 2, f"{pair_path}: run count mismatch")
    require(aggregate["pair_count"] == 1, f"{pair_path}: pair count mismatch")
    require(len(pair["runs"]) == 2, f"{pair_path}: runs length mismatch")
    require(len(pair["pairs"]) == 1, f"{pair_path}: pairs length mismatch")
    require(pair["pairs"][0]["comparison_invariants"]["unchecked_fields"] == [], f"{pair_path}: unchecked invariants")
    for run in pair["runs"]:
        context = run.get("comparison_context", {})
        require(context.get("repeat_id") == expected_repeat_id, f"{pair_path}: comparison repeat mismatch")
        require(resolve_repo_path(run["source_path"]).is_file(), f"{pair_path}: missing source findings {run['source_path']}")

    regenerated = compare_contract_runs([load_contract_result(resolve_repo_path(run["source_path"])) for run in pair["runs"]])
    require(regenerated["aggregate"] == aggregate, f"{pair_path}: regenerated aggregate mismatch")
    regenerated_claim = regenerated["pairs"][0]["classification"]["claim"]
    stored_claim = pair["pairs"][0]["classification"]["claim"]
    require(regenerated_claim == stored_claim, f"{pair_path}: classification mismatch")
    require(stored_claim == pair_ref["classification"], f"{pair_path}: stale classification ref")
    require(aggregate["pairwise_disagreements"] == pair_ref["pairwise_disagreements"], f"{pair_path}: stale disagreement ref")
    require(aggregate["runtime_drift_claims"] == pair_ref["runtime_drift_claims"], f"{pair_path}: stale drift ref")
    return aggregate["pairwise_disagreements"], aggregate["runtime_drift_claims"], stored_claim


def validate_case(row: dict[str, Any], repeat_ids: list[int]) -> tuple[int, int, int, int, Counter[str]]:
    case_id = row["case_id"]
    require(row.get("repeat_ids") == repeat_ids, f"{case_id}: repeat IDs mismatch")
    observation_count = 0
    pair_count = 0
    pairwise_disagreements = 0
    runtime_drift_claims = 0
    classifications: Counter[str] = Counter()

    for runtime in ("RP2", "RP3"):
        runtime_summary = row["runtime_summaries"][runtime]
        observations = runtime_summary["observations"]
        require(len(observations) == len(repeat_ids), f"{case_id}/{runtime}: observation count mismatch")
        summaries = [
            validate_observation(case_id, observation, repeat_id, runtime)
            for observation, repeat_id in zip(observations, repeat_ids, strict=True)
        ]
        first = summaries[0]
        first_without_event_count = summary_without_event_count(first)
        stability = runtime_summary["stability"]
        require(
            stability["event_counts"] == {str(repeat_id): summary["event_count"] for repeat_id, summary in zip(repeat_ids, summaries, strict=True)},
            f"{case_id}/{runtime}: stale event-count map",
        )
        require(
            stability["stable_summary_excluding_event_count"]
            == all(summary_without_event_count(summary) == first_without_event_count for summary in summaries),
            f"{case_id}/{runtime}: stale excluding-event-count stability",
        )
        require(
            stability["stable_summary_including_event_count"] == all(summary == first for summary in summaries),
            f"{case_id}/{runtime}: stale including-event-count stability",
        )
        require(
            stability["max_realized_contract_violations"] == max(summary["realized_contract_violations"] for summary in summaries),
            f"{case_id}/{runtime}: realized max",
        )
        require(
            stability["max_attempted_overreach"] == max(summary["attempted_overreach"] for summary in summaries),
            f"{case_id}/{runtime}: attempted max",
        )
        require(
            stability["max_missing_expected_outputs"] == max(summary["missing_expected_outputs"] for summary in summaries),
            f"{case_id}/{runtime}: missing max",
        )
        require(
            stability["max_output_oracle_failures"] == max(summary["output_oracle_failures"] for summary in summaries),
            f"{case_id}/{runtime}: oracle max",
        )
        require(
            stability["max_canary_observation_count"] == max(summary["canary_observation_count"] for summary in summaries),
            f"{case_id}/{runtime}: canary max",
        )
        observation_count += len(observations)

    pairs = row["same_repeat_pairs"]
    require(len(pairs) == len(repeat_ids), f"{case_id}: pair count mismatch")
    for pair, repeat_id in zip(pairs, repeat_ids, strict=True):
        disagreements, drift_claims, classification = validate_pair(pair, repeat_id)
        pair_count += 1
        pairwise_disagreements += disagreements
        runtime_drift_claims += drift_claims
        classifications[classification] += 1
    return observation_count, pair_count, pairwise_disagreements, runtime_drift_claims, classifications


def parse_repeat_ids(values: list[int]) -> list[int]:
    repeat_ids = values or list(DEFAULT_REPEAT_IDS)
    repeat_ids = sorted(set(repeat_ids))
    require(all(repeat_id > 0 for repeat_id in repeat_ids), "repeat IDs must be positive integers")
    return repeat_ids


def validate_report(families: list[str], case_ids: list[str], repeat_ids: list[int]) -> None:
    require(REPORT_PATH.is_file(), f"missing {REPORT_PATH}")
    report = load_json(REPORT_PATH)
    require(report["report_type"] == "main_rp2_rp3_repeat_stability", "unexpected report type")
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

    expected_cases = select_cases(current_cases(), families, case_ids)
    require(expected_cases, "no current main RP2/RP3 cases selected")
    expected_case_ids = [case["case_id"] for case in expected_cases]

    cases = report["cases"]
    require([row["case_id"] for row in cases] == expected_case_ids, "case selection or ordering mismatch")
    observation_count = 0
    pair_count = 0
    pairwise_disagreements = 0
    runtime_drift_claims = 0
    classifications: Counter[str] = Counter()
    stable_excluding = 0
    stable_including = 0

    for row in cases:
        for runtime in ("RP2", "RP3"):
            stability = row["runtime_summaries"][runtime]["stability"]
            if stability["stable_summary_excluding_event_count"]:
                stable_excluding += 1
            if stability["stable_summary_including_event_count"]:
                stable_including += 1
        observations, pairs, disagreements, drift_claims, case_classifications = validate_case(row, repeat_ids)
        observation_count += observations
        pair_count += pairs
        pairwise_disagreements += disagreements
        runtime_drift_claims += drift_claims
        classifications.update(case_classifications)

    aggregate = report["aggregate"]
    expected_observations = len(expected_cases) * len(repeat_ids) * 2
    expected_pairs = len(expected_cases) * len(repeat_ids)
    require(aggregate["case_count"] == len(expected_cases), "aggregate case count mismatch")
    require(aggregate["repeat_ids"] == repeat_ids, "aggregate repeat IDs mismatch")
    require(aggregate["runtime_profiles"] == ["RP2", "RP3"], "aggregate runtime profiles mismatch")
    require(aggregate["runtime_observation_count"] == expected_observations, "aggregate observation count mismatch")
    require(aggregate["trace_valid_count"] == expected_observations, "aggregate trace count mismatch")
    require(aggregate["findings_file_count"] == expected_observations, "aggregate findings count mismatch")
    require(aggregate["same_repeat_pair_count"] == expected_pairs, "aggregate pair count mismatch")
    require(aggregate["classification_counts"] == dict(sorted(classifications.items())), "classification counts mismatch")
    require(aggregate["pairwise_disagreement_count"] == pairwise_disagreements, "aggregate disagreement count mismatch")
    require(aggregate["runtime_drift_claim_count"] == runtime_drift_claims, "aggregate drift claim count mismatch")
    require(aggregate["case_runtime_stability_units"] == len(expected_cases) * 2, "stability unit count mismatch")
    require(
        aggregate["summary_match_count_excluding_event_count"] == stable_excluding,
        "excluding-event-count stability mismatch",
    )
    require(
        aggregate["summary_match_count_including_event_count"] == stable_including,
        "including-event-count stability mismatch",
    )
    require(
        aggregate["minimum_repeats_for_deterministic_stability_claim"] == len(repeat_ids),
        "minimum repeat count mismatch",
    )
    require(aggregate["statistical_repeat_stability_claims_supported"] == 0, "statistics claim must remain zero")
    require(observation_count == expected_observations, "validated observation count mismatch")
    require(pair_count == expected_pairs, "validated pair count mismatch")
    repeat_comparison_glob = list(RESULTS_ROOT.glob("**/*_comparison.json"))
    require(repeat_comparison_glob == [], f"repeat artifact leaked into comparison glob: {repeat_comparison_glob[:3]}")
    print(
        "validated main repeat stability: "
        f"{len(expected_cases)} cases, {expected_observations} observations, {expected_pairs} pairs"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat-id", action="append", type=int, default=[], help="Repeat ID to validate.")
    parser.add_argument("--family", action="append", default=[], help="Restrict validation to one or more family IDs.")
    parser.add_argument("--case-id", action="append", default=[], help="Restrict validation to one or more case IDs.")
    args = parser.parse_args(argv)
    repeat_ids = parse_repeat_ids(args.repeat_id)
    validate_report(args.family, args.case_id, repeat_ids)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"main repeat-stability validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
