"""Pairwise comparison metrics for contract-check outputs."""

from __future__ import annotations

from itertools import combinations
from pathlib import Path
from typing import Any
import json


STRICT_COMPARISON_FIELDS = ("skill_id", "task_id", "contract_id", "repeat_id")
PLANNED_COMPARISON_FIELDS = ("workspace_snapshot_hash", "task_prompt_hash", "variant_id")


def load_contract_result(path: Path) -> dict[str, Any]:
    """Load one contract-check result and attach its source path."""
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    for key in ("run_id", "runtime_profile", "summary", "findings"):
        if key not in data:
            raise ValueError(f"{path} is missing required key: {key}")
    data = dict(data)
    data["source_path"] = _display_path(path)
    data["trace_context"] = _load_trace_context(data.get("trace_path"))
    return data


def compare_contract_runs(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare two or more contract-check result objects."""
    if len(results) < 2:
        raise ValueError("at least two contract-check results are required")

    normalized_runs = [_run_summary(result, index) for index, result in enumerate(results)]
    pairs = [
        _pairwise_comparison(left, right)
        for left, right in combinations(normalized_runs, 2)
    ]
    aggregate = {
        "run_count": len(normalized_runs),
        "pair_count": len(pairs),
        "runtime_profiles": sorted({run["runtime_profile"] for run in normalized_runs}),
        "contract_ids": sorted({run["contract_id"] for run in normalized_runs}),
        "drift_classes_observed": sorted(
            {drift_class for run in normalized_runs for drift_class in run["drift_classes_observed"]}
        ),
        "pairwise_disagreements": sum(pair["disagreement_count"] for pair in pairs),
        "runtime_drift_claims": sum(1 for pair in pairs if pair["classification"]["claim"] == "runtime_drift_candidate"),
    }
    return {
        "report_type": "contract_run_pairwise_comparison",
        "schema_version": 1,
        "aggregate": aggregate,
        "runs": normalized_runs,
        "pairs": pairs,
    }


def _run_summary(result: dict[str, Any], index: int) -> dict[str, Any]:
    findings = result.get("findings") or []
    if not isinstance(findings, list):
        raise ValueError(f"run at index {index} has non-list findings")
    signatures = _merge_signatures([_finding_signature(finding) for finding in findings])
    return {
        "index": index,
        "run_id": result["run_id"],
        "runtime_profile": result["runtime_profile"],
        "contract_id": result.get("contract_id", "unknown"),
        "comparison_context": _comparison_context(result),
        "trace_path": result.get("trace_path"),
        "source_path": result.get("source_path"),
        "summary": {
            "event_count": _summary_int(result, "event_count"),
            "realized_contract_violations": _summary_int(result, "realized_contract_violations"),
            "attempted_overreach": _summary_int(result, "attempted_overreach"),
            "canary_observation_count": _summary_int(result, "canary_observation_count"),
            "trace_valid": bool(result.get("summary", {}).get("trace_valid", False)),
        },
        "drift_classes_observed": sorted(
            {drift_class for finding in findings for drift_class in finding.get("drift_classes", [])}
        ),
        "finding_count": len(findings),
        "finding_signatures": sorted(signatures, key=_signature_sort_key),
    }


def _summary_int(result: dict[str, Any], key: str) -> int:
    value = result.get("summary", {}).get(key, 0)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{result.get('run_id', '<unknown>')} summary.{key} must be an integer")
    return value


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return str(path)


def _load_trace_context(trace_path: str | None) -> dict[str, Any]:
    if not trace_path:
        return {}
    path = Path(trace_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    try:
        with path.open("r", encoding="utf-8") as handle:
            first_line = handle.readline()
    except FileNotFoundError:
        return {"trace_context_error": "trace_path_not_found"}
    if not first_line:
        return {"trace_context_error": "trace_empty"}
    try:
        event = json.loads(first_line)
    except json.JSONDecodeError:
        return {"trace_context_error": "trace_first_event_not_json"}

    return {
        "skill_id": event.get("skill_id"),
        "task_id": event.get("task_id"),
        "contract_id": event.get("contract_id"),
        "repeat_id": event.get("repeat_id"),
        "runtime_profile_hash": event.get("runtime_profile_hash"),
    }


def _comparison_context(result: dict[str, Any]) -> dict[str, Any]:
    trace_context = result.get("trace_context") or {}
    context = {
        "skill_id": result.get("skill_id") or trace_context.get("skill_id"),
        "task_id": result.get("task_id") or trace_context.get("task_id"),
        "contract_id": result.get("contract_id") or trace_context.get("contract_id"),
        "repeat_id": result.get("repeat_id") or trace_context.get("repeat_id"),
        "workspace_snapshot_hash": result.get("workspace_snapshot_hash"),
        "task_prompt_hash": result.get("task_prompt_hash"),
        "variant_id": result.get("variant_id"),
        "runtime_profile_hash": result.get("runtime_profile_hash") or trace_context.get("runtime_profile_hash"),
    }
    missing = [field for field in (*STRICT_COMPARISON_FIELDS, *PLANNED_COMPARISON_FIELDS) if context.get(field) is None]
    context["missing_invariant_fields"] = missing
    return context


def _finding_signature(finding: dict[str, Any]) -> dict[str, Any]:
    drift_classes = sorted(finding.get("drift_classes") or [])
    canary_labels = sorted(finding.get("canary_labels") or [])
    return {
        "finding_type": finding.get("finding_type"),
        "event_type": finding.get("event_type"),
        "rule_id": finding.get("rule_id"),
        "severity": finding.get("severity"),
        "target": finding.get("target"),
        "drift_classes": drift_classes,
        "canary_labels": canary_labels,
        "event_ids": sorted([finding["event_id"]]) if finding.get("event_id") else [],
    }


def _merge_signatures(signatures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[Any, ...], dict[str, Any]] = {}
    for signature in signatures:
        key = _signature_key(signature)
        if key not in merged:
            merged[key] = dict(signature)
            continue
        merged[key]["event_ids"] = sorted(set(merged[key]["event_ids"]) | set(signature["event_ids"]))
    return list(merged.values())


def _pairwise_comparison(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_keys = {_signature_key(signature): signature for signature in left["finding_signatures"]}
    right_keys = {_signature_key(signature): signature for signature in right["finding_signatures"]}
    shared_keys = sorted(left_keys.keys() & right_keys.keys())
    only_left_keys = sorted(left_keys.keys() - right_keys.keys())
    only_right_keys = sorted(right_keys.keys() - left_keys.keys())
    only_left = [left_keys[key] for key in only_left_keys]
    only_right = [right_keys[key] for key in only_right_keys]
    return {
        "left_run_id": left["run_id"],
        "right_run_id": right["run_id"],
        "left_runtime_profile": left["runtime_profile"],
        "right_runtime_profile": right["runtime_profile"],
        "contract_id_match": left["contract_id"] == right["contract_id"],
        "comparison_invariants": _pair_invariants(left, right),
        "classification": _classify_pair(left, right, only_left, only_right),
        "shared_finding_count": len(shared_keys),
        "disagreement_count": len(only_left) + len(only_right),
        "only_in_left": only_left,
        "only_in_right": only_right,
        "summary_delta": {
            "realized_contract_violations": right["summary"]["realized_contract_violations"]
            - left["summary"]["realized_contract_violations"],
            "attempted_overreach": right["summary"]["attempted_overreach"] - left["summary"]["attempted_overreach"],
            "canary_observation_count": right["summary"]["canary_observation_count"]
            - left["summary"]["canary_observation_count"],
            "event_count": right["summary"]["event_count"] - left["summary"]["event_count"],
        },
    }


def _pair_invariants(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_context = left.get("comparison_context", {})
    right_context = right.get("comparison_context", {})
    strict_mismatches = []
    unchecked = []
    for field in STRICT_COMPARISON_FIELDS:
        left_value = left_context.get(field)
        right_value = right_context.get(field)
        if left_value is None or right_value is None:
            unchecked.append(field)
        elif left_value != right_value:
            strict_mismatches.append({"field": field, "left": left_value, "right": right_value})
    for field in PLANNED_COMPARISON_FIELDS:
        left_value = left_context.get(field)
        right_value = right_context.get(field)
        if left_value is None or right_value is None:
            unchecked.append(field)
        elif left_value != right_value:
            strict_mismatches.append({"field": field, "left": left_value, "right": right_value})
    return {
        "strict_fields": list(STRICT_COMPARISON_FIELDS),
        "planned_fields": list(PLANNED_COMPARISON_FIELDS),
        "strict_mismatches": strict_mismatches,
        "unchecked_fields": sorted(set(unchecked)),
    }


def _classify_pair(
    left: dict[str, Any],
    right: dict[str, Any],
    only_left: list[dict[str, Any]],
    only_right: list[dict[str, Any]],
) -> dict[str, str]:
    invariants = _pair_invariants(left, right)
    if invariants["strict_mismatches"]:
        mismatches = ", ".join(mismatch["field"] for mismatch in invariants["strict_mismatches"])
        return {
            "claim": "not_comparable",
            "boundary": f"Compared runs differ on required invariant(s): {mismatches}. Disagreements are not runtime drift evidence.",
        }
    if left["runtime_profile"] == right["runtime_profile"]:
        return {
            "claim": "same_runtime_scenario_difference",
            "boundary": "Both runs use the same runtime profile; disagreements can show scenario or input differences but not runtime-induced drift.",
        }
    if not only_left and not only_right:
        return {
            "claim": "no_pairwise_disagreement",
            "boundary": "Runtime profiles differ, but this pair has no finding-set disagreement in the observed contract-check output.",
        }
    return {
        "claim": "runtime_drift_candidate",
        "boundary": "Runtime profiles differ with matching available skill/task/contract/repeat invariants. Treat this as a runtime-drift candidate; workspace snapshot, prompt hash, and variant ID remain planned comparator invariants until emitted by the runners.",
    }


def _signature_key(signature: dict[str, Any]) -> tuple[Any, ...]:
    return (
        signature["finding_type"],
        signature["event_type"],
        signature["rule_id"],
        signature["severity"],
        signature["target"],
        tuple(signature["drift_classes"]),
        tuple(signature["canary_labels"]),
    )


def _signature_sort_key(signature: dict[str, Any]) -> tuple[Any, ...]:
    return _signature_key(signature) + (tuple(signature["event_ids"]),)
