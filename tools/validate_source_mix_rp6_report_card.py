#!/usr/bin/env python3
"""Validate source-mix RP6 report-card evidence."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "benchmark" / "manifests" / "benchmark-cases-current.json"
REPORT_ROOT = REPO_ROOT / "results" / "fixtures" / "strengthening" / "source-mix-rp6-report-card"
REPORT_CARD = REPORT_ROOT / "report_card.json"
EXECUTION_LEVEL = "controlled_single_repeat_fixture_rp2_rp3"
SOURCE_LABELS = {"first_party", "public"}
REPEAT_IDS = (1, 2, 3)
LOCAL_PATH_PATTERNS = [
    re.compile(pattern)
    for pattern in (
        "/" + r"Users/[^/\s\"']+",
        "/" + "private/" + r"var/folders/[^\s\"']+",
        "/" + "var/" + r"folders/[^\s\"']+",
    )
]
TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".txt", ".yaml", ".yml"}
EXPECTED_AGGREGATE = {
    "case_count": 74,
    "family_count": 26,
    "source_mix_counts": {"first_party": 25, "public": 49},
    "rp6_completed_cases": 74,
    "rp6_realized_contract_violations": 0,
    "rp6_attempted_overreach": 0,
    "rp6_missing_expected_outputs": 0,
    "rp6_output_oracle_failures": 0,
    "rp6_canary_observations": 0,
}

sys.path.insert(0, str(REPO_ROOT / "src"))

from skilldiff.metrics.contract_compare import compare_contract_runs, load_contract_result  # noqa: E402
from skilldiff.traces import validate_trace_file  # noqa: E402


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def resolve_repo_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")


def repeat_stem(stem: str, repeat_id: int) -> str:
    if repeat_id == 1:
        return stem
    return f"{stem}_repeat{repeat_id}"


def result_stem(case: dict[str, Any]) -> str:
    return slug(case["provenance"]["task_id"])


def expected_comparison_path(case: dict[str, Any], repeat_id: int) -> Path:
    stem = repeat_stem(f"{result_stem(case)}_rp2_rp3_rp6_comparison", repeat_id)
    return REPORT_ROOT / case["family_id"] / f"{stem}.json"


def source_mix_cases() -> list[dict[str, Any]]:
    manifest = load_json(MANIFEST_PATH)
    return sorted(
        [
            case
            for case in manifest.get("cases", [])
            if case.get("execution", {}).get("execution_level") == EXECUTION_LEVEL
            and case.get("provenance", {}).get("source_mix", {}).get("label") in SOURCE_LABELS
        ],
        key=lambda case: (case["family_id"], case["provenance"]["task_id"]),
    )


def expected_case_ids() -> set[str]:
    return {case["case_id"] for case in source_mix_cases()}


def validate_report_card() -> dict[str, Any]:
    report = load_json(REPORT_CARD)
    require(report.get("schema_version") == "0.1", "report_card schema_version mismatch")
    require(report.get("report_type") == "source_mix_rp6_report_card", "report_card type mismatch")
    boundary = str(report.get("boundary") or "")
    for phrase in (
        "Broader RP6 profile-backed report-card evidence",
        "not live product behavior",
        "source-mix completion",
        "defense success",
        "commercial-runtime behavior",
        "public-network behavior",
        "prevalence evidence",
        "human adjudication evidence",
    ):
        require(phrase in boundary, f"boundary missing phrase {phrase!r}")

    aggregate = report.get("aggregate", {})
    for key, expected in EXPECTED_AGGREGATE.items():
        require(aggregate.get(key) == expected, f"aggregate {key} mismatch: {aggregate.get(key)!r}")
    cases = report.get("cases")
    require(isinstance(cases, list) and len(cases) == EXPECTED_AGGREGATE["case_count"], "unexpected case count")
    observed_ids = {case.get("case_id") for case in cases}
    require(observed_ids == expected_case_ids(), "report-card case IDs do not match manifest source-mix cases")
    return report


def validate_case_rows(report: dict[str, Any]) -> None:
    for row in report["cases"]:
        key = (row.get("family"), row.get("task_id"))
        require(row.get("source_mix_label") in SOURCE_LABELS, f"{key}: unexpected source mix")
        require(row.get("runtime_profile") == "RP6", f"{key}: runtime profile is not RP6")
        summary = row.get("summary", {})
        require(summary.get("trace_valid") is True, f"{key}: trace_valid is not true")
        for field in (
            "realized_contract_violations",
            "attempted_overreach",
            "missing_expected_outputs",
            "output_oracle_failures",
            "canary_observation_count",
        ):
            require(summary.get(field) == 0, f"{key}: expected {field}=0")

        findings_path = resolve_repo_path(row["findings_path"])
        trace_path = resolve_repo_path(row["trace_path"])
        require(findings_path.is_file(), f"{key}: missing findings {findings_path}")
        require(trace_path.is_file(), f"{key}: missing trace {trace_path}")
        findings = load_json(findings_path)
        require(findings.get("summary") == summary, f"{key}: stale findings summary")
        require(findings.get("comparison_role") == "mitigation_report_card", f"{key}: comparison role missing")
        require(findings.get("evidence_scope") == "source_mix_rp6_report_card_fixture", f"{key}: evidence scope mismatch")

        events = validate_trace_file(trace_path)
        require(len(events) == summary["event_count"], f"{key}: trace event count mismatch")
        require({event["runtime_profile"] for event in events} == {"RP6"}, f"{key}: trace has non-RP6 event")
        require({event["adapter_id"] for event in events} == {"hardened_policy_adapter"}, f"{key}: wrong adapter")
        require(any(event["event_type"] == "activation.select" for event in events), f"{key}: missing activation.select")


def validate_comparisons(report: dict[str, Any]) -> None:
    expected_paths = {
        expected_comparison_path(case, repeat_id)
        for case in source_mix_cases()
        for repeat_id in REPEAT_IDS
    }
    comparison_paths = set(REPORT_ROOT.glob("*/*_rp2_rp3_rp6_comparison*.json"))
    require(
        comparison_paths == expected_paths,
        (
            "unexpected comparison file set: "
            f"missing={sorted(str(path.relative_to(REPO_ROOT)) for path in expected_paths - comparison_paths)[:3]} "
            f"extra={sorted(str(path.relative_to(REPO_ROOT)) for path in comparison_paths - expected_paths)[:3]}"
        ),
    )
    require(
        len(comparison_paths) == EXPECTED_AGGREGATE["case_count"] * len(REPEAT_IDS),
        "unexpected comparison count",
    )
    for path in sorted(comparison_paths):
        repeat_id = 1
        match = re.search(r"_repeat(\d+)\.json$", path.name)
        if match:
            repeat_id = int(match.group(1))
        require(repeat_id in REPEAT_IDS, f"{path}: unexpected repeat id")
        comparison = load_json(path)
        aggregate = comparison.get("aggregate", {})
        require(aggregate.get("run_count") == 3, f"{path}: expected 3 runs")
        require(aggregate.get("pair_count") == 3, f"{path}: expected 3 pairs")
        require(aggregate.get("runtime_profiles") == ["RP2", "RP3", "RP6"], f"{path}: runtime profiles mismatch")
        source_paths = []
        for run in comparison.get("runs", []):
            source_path = resolve_repo_path(run["source_path"])
            trace_path = resolve_repo_path(run["trace_path"])
            require(source_path.is_file(), f"{path}: missing source {source_path}")
            source_paths.append(source_path)
            context = run.get("comparison_context", {})
            runtime_profile = run.get("runtime_profile")
            summary = run.get("summary", {})
            require(summary.get("trace_valid") is True, f"{path}: {runtime_profile} trace_valid is not true")
            if trace_path.is_file():
                events = validate_trace_file(trace_path)
                require(any(event["event_type"] == "activation.select" for event in events), f"{path}: missing activation")
            else:
                require(
                    runtime_profile in {"RP2", "RP3"},
                    f"{path}: missing required RP6 report-card trace {trace_path}",
                )
            expected_repeat_id = repeat_id if runtime_profile == "RP6" else 1
            require(
                context.get("repeat_id") == expected_repeat_id,
                f"{path}: {runtime_profile} repeat_id is not {expected_repeat_id}",
            )
            require(context.get("missing_invariant_fields") == [], f"{path}: missing invariant fields")
        for pair in comparison.get("pairs", []):
            invariants = pair.get("comparison_invariants", {})
            require(invariants.get("unchecked_fields") == [], f"{path}: unchecked invariant fields")
            profiles = {pair.get("left_runtime_profile"), pair.get("right_runtime_profile")}
            strict_mismatches = invariants.get("strict_mismatches")
            claim = pair.get("classification", {}).get("claim")
            if repeat_id == 1 or "RP6" not in profiles:
                require(strict_mismatches == [], f"{path}: strict invariant mismatch")
            else:
                require(
                    strict_mismatches
                    == [{"field": "repeat_id", "left": 1, "right": repeat_id}],
                    f"{path}: unexpected repeat comparison mismatch",
                )
                require(claim == "not_comparable", f"{path}: repeat-mismatched RP6 pair must be non-comparable")
            if "RP6" in profiles:
                if repeat_id == 1:
                    require(claim == "mitigation_report_card_comparison", f"{path}: RP6 pair is not mitigation-only")
        regenerated = compare_contract_runs([load_contract_result(source_path) for source_path in source_paths])
        require(regenerated.get("aggregate") == aggregate, f"{path}: regenerated aggregate mismatch")


def validate_no_local_paths() -> None:
    findings: list[str] = []
    for path in sorted(REPORT_ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if any(pattern.search(line) for pattern in LOCAL_PATH_PATTERNS):
                findings.append(f"{path.relative_to(REPO_ROOT)}:{line_no}")
                break
    require(not findings, f"source-mix RP6 local path leakage: {findings[:5]}")


def main() -> int:
    report = validate_report_card()
    validate_case_rows(report)
    validate_comparisons(report)
    validate_no_local_paths()
    print(
        "validated source-mix RP6 report-card evidence: "
        f"{EXPECTED_AGGREGATE['case_count']} cases, {EXPECTED_AGGREGATE['family_count']} families"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"source-mix RP6 validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
