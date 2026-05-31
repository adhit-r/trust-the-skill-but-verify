#!/usr/bin/env python3
"""Validate repeat-backed coverage and explicit repeat-claim exclusions."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "benchmark" / "manifests" / "benchmark-cases-current.json"
PLANNED_REPEAT_PATH = (
    REPO_ROOT / "results" / "fixtures" / "strengthening" / "rp2-rp3-repeat-stability" / "repeat_stability.json"
)
MAIN_REPEAT_PATH = (
    REPO_ROOT / "results" / "fixtures" / "strengthening" / "rp2-rp3-main-repeat-stability" / "repeat_stability.json"
)
RP6_REPEAT_PATH = REPO_ROOT / "results" / "fixtures" / "strengthening" / "repeat-stability" / "repeat_stability.json"
SOURCE_MIX_RP6_REPEAT_PATH = (
    REPO_ROOT
    / "results"
    / "fixtures"
    / "strengthening"
    / "source-mix-rp6-repeat-stability"
    / "repeat_stability.json"
)
RP1_REPORT_CARD_PATH = REPO_ROOT / "results" / "fixtures" / "rp1-restricted-hosted" / "report_card.json"
RP5_REPORT_CARD_PATH = REPO_ROOT / "results" / "fixtures" / "rp5-plugin-style" / "report_card.json"
RP1_DERIVED_CARD_PATH = REPO_ROOT / "results" / "derived" / "runtime-report-cards" / "rp1_report_card.json"
RP5_DERIVED_CARD_PATH = REPO_ROOT / "results" / "derived" / "runtime-report-cards" / "rp5_report_card.json"
GATE5_INTERVAL_PATH = REPO_ROOT / "results" / "derived" / "gate5-statistical-intervals.json"
METHOD_BOUNDARY_PATH = REPO_ROOT / "paper" / "method-boundaries.md"

PLANNED_EXECUTION_LEVEL = "controlled_single_repeat_fixture_rp2_rp3"
MAIN_EXECUTION_LEVELS = {
    "controlled_python_fixture_rp2_rp3",
    "controlled_python_fixture_rp2_rp3_negative_control",
    "controlled_python_fixture_rp2_rp3_semantic_event_fixture",
    "controlled_python_fixture_rp2_rp3_local_fake_sink",
}
RP5_EXECUTION_LEVELS = {
    "plugin_fixture_rp5_report_card",
    "plugin_fixture_rp5_report_card_negative_control",
}
EXPECTED_REPEAT_IDS = [1, 2, 3]
CLAIM_BOUNDARY_FALSE_KEYS = (
    "completed_statistics_claimed",
    "reviewer_adjudication_claimed",
    "prevalence_claim",
    "defense_success_claim",
    "live_product_claim",
    "commercial_runtime_claim",
    "public_network_claim",
)
MAX_STABILITY_KEYS = (
    "max_realized_contract_violations",
    "max_attempted_overreach",
    "max_missing_expected_outputs",
    "max_output_oracle_failures",
    "max_canary_observation_count",
)
MODEL_MEDIATED_MARKERS = (
    "model_mediated",
    "model-mediated",
    "nondeterministic",
    "non_deterministic",
)


def load_json(path: Path) -> Any:
    if not path.is_file():
        raise AssertionError(f"missing {repo_path(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


def repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def manifest_cases() -> list[dict[str, Any]]:
    manifest = load_json(MANIFEST_PATH)
    cases = manifest.get("cases")
    require(isinstance(cases, list), "benchmark manifest must contain a cases list")
    return cases


def planned_repeat_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        (
            case
            for case in cases
            if case.get("execution", {}).get("execution_level") == PLANNED_EXECUTION_LEVEL
            and "planned" in case.get("provenance", {}).get("source_manifest_ref", "")
        ),
        key=lambda case: case["case_id"],
    )


def main_repeat_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        (
            case
            for case in cases
            if case.get("execution", {}).get("execution_level") in MAIN_EXECUTION_LEVELS
            and "planned" not in case.get("provenance", {}).get("source_manifest_ref", "")
        ),
        key=lambda case: (case["family_id"], case["provenance"]["task_id"]),
    )


def rp5_manifest_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        (case for case in cases if case.get("execution", {}).get("execution_level") in RP5_EXECUTION_LEVELS),
        key=lambda case: case["case_id"],
    )


def metadata_only_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        (
            case
            for case in cases
            if case.get("execution", {}).get("execution_level") == "inclusion_planning_only_not_executed"
        ),
        key=lambda case: case["case_id"],
    )


def model_mediated_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for case in cases:
        haystack = json.dumps(case.get("execution", {}), sort_keys=True).lower()
        haystack += " " + json.dumps(case.get("provenance", {}), sort_keys=True).lower()
        if any(marker in haystack for marker in MODEL_MEDIATED_MARKERS):
            selected.append(case)
    return selected


def validate_claim_boundary(report: dict[str, Any], label: str) -> None:
    claim_boundary = report.get("claim_boundary")
    require(isinstance(claim_boundary, dict), f"{label}: missing claim_boundary object")
    for key in CLAIM_BOUNDARY_FALSE_KEYS:
        require(claim_boundary.get(key) is False, f"{label}: claim boundary {key} must be false")


def validate_max_fields(rows: list[dict[str, Any]], label: str) -> None:
    for row in rows:
        for runtime in ("RP2", "RP3"):
            stability = row.get("runtime_summaries", {}).get(runtime, {}).get("stability", {})
            for key in MAX_STABILITY_KEYS:
                require(isinstance(stability.get(key), int), f"{label}/{row.get('case_id')}/{runtime}: missing {key}")


def validate_rp2_rp3_repeat_report(
    *,
    label: str,
    path: Path,
    report_type: str,
    expected_cases: list[dict[str, Any]],
    require_zero_pairwise_drift: bool,
) -> dict[str, int]:
    report = load_json(path)
    validate_claim_boundary(report, label)
    require(report.get("report_type") == report_type, f"{label}: unexpected report type")
    rows = report.get("cases")
    require(isinstance(rows, list), f"{label}: cases must be a list")
    expected_case_ids = [case["case_id"] for case in expected_cases]
    metadata_only_ids = {case["case_id"] for case in metadata_only_cases(manifest_cases())}
    actual_case_ids = [row.get("case_id") for row in rows]
    require(len(actual_case_ids) == len(set(actual_case_ids)), f"{label}: duplicate repeat rows")
    require(
        set(actual_case_ids) == set(expected_case_ids),
        f"{label}: repeat rows do not match benchmark manifest case set",
    )
    require(
        not (set(actual_case_ids) & metadata_only_ids),
        f"{label}: metadata-only cases leaked into repeat coverage",
    )
    validate_max_fields(rows, label)

    case_count = len(expected_cases)
    aggregate = report.get("aggregate", {})
    expected_observations = case_count * len(EXPECTED_REPEAT_IDS) * 2
    expected_pairs = case_count * len(EXPECTED_REPEAT_IDS)
    expected_case_runtime_units = case_count * 2
    require(aggregate.get("case_count") == case_count, f"{label}: aggregate case count mismatch")
    require(aggregate.get("repeat_ids") == EXPECTED_REPEAT_IDS, f"{label}: repeat IDs mismatch")
    require(aggregate.get("runtime_profiles") == ["RP2", "RP3"], f"{label}: runtime profiles mismatch")
    require(
        aggregate.get("runtime_observation_count") == expected_observations,
        f"{label}: runtime observation count mismatch",
    )
    require(aggregate.get("trace_valid_count") == expected_observations, f"{label}: trace-valid count mismatch")
    require(aggregate.get("findings_file_count") == expected_observations, f"{label}: findings count mismatch")
    require(aggregate.get("same_repeat_pair_count") == expected_pairs, f"{label}: pair count mismatch")
    require(
        aggregate.get("case_runtime_stability_units") == expected_case_runtime_units,
        f"{label}: stability unit count mismatch",
    )
    require(
        aggregate.get("summary_match_count_excluding_event_count") == expected_case_runtime_units,
        f"{label}: excluding-event-count stability mismatch",
    )
    require(
        aggregate.get("minimum_repeats_for_deterministic_stability_claim") == len(EXPECTED_REPEAT_IDS),
        f"{label}: minimum repeat count mismatch",
    )
    require(
        aggregate.get("statistical_repeat_stability_claims_supported") == 0,
        f"{label}: statistical repeat-stability claims must remain zero",
    )
    if require_zero_pairwise_drift:
        require(aggregate.get("pairwise_disagreement_count") == 0, f"{label}: expected zero pairwise disagreements")
        require(aggregate.get("runtime_drift_claim_count") == 0, f"{label}: expected zero runtime-drift claims")
    return {
        "case_count": case_count,
        "runtime_observation_count": expected_observations,
        "same_repeat_pair_count": expected_pairs,
    }


def validate_rp6_repeat_report() -> dict[str, int]:
    report = load_json(RP6_REPEAT_PATH)
    require(report.get("report_type") == "rp6_repeat_stability", "RP6 repeat: unexpected report type")
    boundary = str(report.get("boundary") or "")
    for required in ("Bounded deterministic", "not a prevalence", "statistical", "model-mediated"):
        require(required in boundary, f"RP6 repeat: missing boundary phrase {required!r}")
    rows = report.get("cases")
    require(isinstance(rows, list) and rows, "RP6 repeat: cases must be a non-empty list")
    aggregate = report.get("aggregate", {})
    case_count = len(rows)
    require(aggregate.get("case_count") == case_count, "RP6 repeat: case count mismatch")
    require(aggregate.get("repeat_ids") == ["1", "2", "3"], "RP6 repeat: repeat IDs mismatch")
    require(aggregate.get("repeats_per_case") == 3, "RP6 repeat: repeats per case mismatch")
    require(aggregate.get("repeat_observation_count") == case_count * 3, "RP6 repeat: observation count mismatch")
    require(aggregate.get("trace_valid_count") == case_count * 3, "RP6 repeat: trace-valid count mismatch")
    require(
        aggregate.get("summary_match_count_excluding_event_count") == case_count,
        "RP6 repeat: excluding-event-count stability mismatch",
    )
    require(
        aggregate.get("deterministic_stability_claims_supported") == case_count,
        "RP6 repeat: deterministic stability count mismatch",
    )
    require(
        aggregate.get("statistical_repeat_stability_claims_supported") == 0,
        "RP6 repeat: statistical repeat-stability claims must remain zero",
    )
    return {"case_count": case_count, "runtime_observation_count": case_count * 3}


def validate_source_mix_rp6_repeat_report() -> dict[str, int]:
    report = load_json(SOURCE_MIX_RP6_REPEAT_PATH)
    require(
        report.get("report_type") == "source_mix_rp6_repeat_stability",
        "source-mix RP6 repeat: unexpected report type",
    )
    boundary = str(report.get("boundary") or "")
    for required in (
        "Bounded deterministic",
        "source-mix RP6",
        "not source-mix completion",
        "statistical",
        "model-mediated",
        "human adjudication",
    ):
        require(required in boundary, f"source-mix RP6 repeat: missing boundary phrase {required!r}")
    validate_claim_boundary(report, "source-mix RP6 repeat")
    claim_boundary = report.get("claim_boundary", {})
    require(
        claim_boundary.get("source_mix_completion_claimed") is False,
        "source-mix RP6 repeat: source-mix completion claim must be false",
    )
    require(
        claim_boundary.get("runtime_drift_claim") is False,
        "source-mix RP6 repeat: runtime-drift claim must be false",
    )
    rows = report.get("cases")
    require(isinstance(rows, list) and rows, "source-mix RP6 repeat: cases must be a non-empty list")
    aggregate = report.get("aggregate", {})
    case_count = len(rows)
    require(aggregate.get("case_count") == case_count, "source-mix RP6 repeat: case count mismatch")
    require(aggregate.get("case_count") == 74, "source-mix RP6 repeat: expected 74 cases")
    require(aggregate.get("family_count") == 26, "source-mix RP6 repeat: expected 26 families")
    require(
        aggregate.get("source_mix_counts") == {"first_party": 25, "public": 49},
        "source-mix RP6 repeat: source mix counts mismatch",
    )
    require(aggregate.get("repeat_ids") == [1, 2, 3], "source-mix RP6 repeat: repeat IDs mismatch")
    require(aggregate.get("repeats_per_case") == 3, "source-mix RP6 repeat: repeats per case mismatch")
    require(
        aggregate.get("repeat_observation_count") == case_count * 3,
        "source-mix RP6 repeat: observation count mismatch",
    )
    require(
        aggregate.get("trace_valid_count") == case_count * 3,
        "source-mix RP6 repeat: trace-valid count mismatch",
    )
    require(
        aggregate.get("stable_summary_excluding_event_count") == case_count,
        "source-mix RP6 repeat: excluding-event-count stability mismatch",
    )
    require(
        aggregate.get("deterministic_stability_claims_supported") == case_count,
        "source-mix RP6 repeat: deterministic stability count mismatch",
    )
    require(
        aggregate.get("statistical_repeat_stability_claims_supported") == 0,
        "source-mix RP6 repeat: statistical repeat-stability claims must remain zero",
    )
    for row in rows:
        require(row.get("observation_count") == 3, f"source-mix RP6 repeat/{row.get('case_id')}: repeat count mismatch")
        require(
            row.get("stable_summary_excluding_event_count") is True,
            f"source-mix RP6 repeat/{row.get('case_id')}: summary stability mismatch",
        )
        require(row.get("source_mix_label") in {"first_party", "public"}, "source-mix RP6 repeat: invalid source mix")
    return {"case_count": case_count, "runtime_observation_count": case_count * 3}


def validate_report_card_exclusion(
    *,
    label: str,
    fixture_path: Path,
    derived_path: Path,
    runtime_profile: str,
    expected_case_count: int | None,
) -> int:
    fixture = load_json(fixture_path)
    derived = load_json(derived_path)
    cases = fixture.get("cases")
    require(isinstance(cases, list) and cases, f"{label}: fixture cases must be a non-empty list")
    case_count = len(cases)
    if expected_case_count is not None:
        require(case_count == expected_case_count, f"{label}: fixture case count mismatch")
    require(fixture.get("aggregate", {}).get("case_count") == case_count, f"{label}: aggregate case count mismatch")
    for row in cases:
        require(row.get("runtime_profile") == runtime_profile, f"{label}: unexpected runtime profile in fixture row")
        require(row.get("summary", {}).get("trace_valid") is True, f"{label}: fixture row is not trace-valid")
        require("repeat_ids" not in row, f"{label}: report-card fixture row must not imply repeat-backed evidence")
    require(derived.get("report_type") == "runtime_report_card", f"{label}: derived card type mismatch")
    require(derived.get("runtime_profile") == runtime_profile, f"{label}: derived card runtime mismatch")
    require(derived.get("aggregate", {}).get("run_count") == case_count, f"{label}: derived run count mismatch")
    boundary = str(derived.get("boundary") or fixture.get("boundary") or "")
    require(boundary, f"{label}: missing report-card boundary text")
    return case_count


def validate_model_mediated_boundary(cases: list[dict[str, Any]]) -> None:
    selected = model_mediated_cases(cases)
    require(
        not selected,
        "model-mediated or nondeterministic benchmark cases need five-repeat evidence before entering repeat-backed claims: "
        + ", ".join(case.get("case_id", "<unknown>") for case in selected[:5]),
    )


def validate_gate5_max_severity_boundary() -> None:
    data = load_json(GATE5_INTERVAL_PATH)
    paired = data.get("paired_runtime_summary", {})
    require("majority_pair_classification" in paired, "Gate 5 intervals: missing majority pair classification")
    require("median_pair_disagreement_count" in paired, "Gate 5 intervals: missing median pair disagreement")
    require("max_pair_severity" in paired, "Gate 5 intervals: missing max pair severity")
    require("pair_max_severity_counts" in paired, "Gate 5 intervals: missing max severity counts")
    require(
        paired["max_pair_severity"] in paired["pair_max_severity_counts"],
        "Gate 5 intervals: max severity absent from severity counts",
    )
    require(
        "not human-adjudicated severity" in paired.get("max_severity_reporting_boundary", ""),
        "Gate 5 intervals: max-severity human-review boundary missing",
    )
    claim_boundary = data.get("claim_boundary", {})
    require(claim_boundary.get("completed_human_review_claimed") is False, "Gate 5 intervals: human review claim")
    require(claim_boundary.get("reviewer_agreement_claimed") is False, "Gate 5 intervals: reviewer agreement claim")
    require(claim_boundary.get("mcnemar_hypothesis_tests_claimed") is False, "Gate 5 intervals: McNemar claim")


def validate_method_boundary_text() -> None:
    text = METHOD_BOUNDARY_PATH.read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    required = (
        "Repeat-backed aggregate claims currently cover four machine-validated buckets",
        "RP1 and RP5 are explicit report-card or fixture evidence, not repeat-backed aggregate evidence",
        "metadata-only source-mix entries",
        "Model-mediated or nondeterministic repeat stability remains unsupported",
    )
    for phrase in required:
        require(phrase in normalized, f"method boundary missing phrase: {phrase}")


def main() -> int:
    cases = manifest_cases()
    metadata_only_count = len(metadata_only_cases(cases))
    validate_model_mediated_boundary(cases)
    planned = validate_rp2_rp3_repeat_report(
        label="planned RP2/RP3 repeat",
        path=PLANNED_REPEAT_PATH,
        report_type="planned_inclusion_rp2_rp3_repeat_stability",
        expected_cases=planned_repeat_cases(cases),
        require_zero_pairwise_drift=True,
    )
    main_report = validate_rp2_rp3_repeat_report(
        label="main RP2/RP3 repeat",
        path=MAIN_REPEAT_PATH,
        report_type="main_rp2_rp3_repeat_stability",
        expected_cases=main_repeat_cases(cases),
        require_zero_pairwise_drift=False,
    )
    rp6 = validate_rp6_repeat_report()
    source_mix_rp6 = validate_source_mix_rp6_repeat_report()
    rp1_case_count = validate_report_card_exclusion(
        label="RP1 simulator report-card exclusion",
        fixture_path=RP1_REPORT_CARD_PATH,
        derived_path=RP1_DERIVED_CARD_PATH,
        runtime_profile="RP1",
        expected_case_count=None,
    )
    rp5_case_count = validate_report_card_exclusion(
        label="RP5 plugin fixture report-card exclusion",
        fixture_path=RP5_REPORT_CARD_PATH,
        derived_path=RP5_DERIVED_CARD_PATH,
        runtime_profile="RP5",
        expected_case_count=len(rp5_manifest_cases(cases)),
    )
    validate_gate5_max_severity_boundary()
    validate_method_boundary_text()
    print(
        "validated repeat coverage: "
        f"{planned['case_count']} planned RP2/RP3 cases, "
        f"{main_report['case_count']} main RP2/RP3 cases, "
        f"{rp6['case_count']} RP6 repeat cases; "
        f"{source_mix_rp6['case_count']} source-mix RP6 repeat cases; "
        f"RP1 report-card-only cases={rp1_case_count}, "
        f"RP5 report-card-only cases={rp5_case_count}, "
        f"metadata-only cases excluded={metadata_only_count}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"repeat coverage validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
