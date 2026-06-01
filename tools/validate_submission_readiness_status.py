#!/usr/bin/env python3
"""Validate the machine-readable submission-readiness status."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = REPO_ROOT / "docs" / "research" / "submission-readiness-status.json"
STATUS_DOC_PATH = REPO_ROOT / "docs" / "research" / "submission-readiness-status.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "research" / "research-roadmap.md"
TODO_PATH = REPO_ROOT / "docs" / "research" / "research-todo.md"
README_PATH = REPO_ROOT / "README.md"
VERIFY_SCRIPT_PATH = REPO_ROOT / "scripts" / "verify_all.sh"

EXPECTED_STATUS = "bounded_non_human_ready_human_review_and_final_refresh_open"
EXPECTED_DATE = "2026-06-01"
EXPECTED_COMPLETED_GATES = {
    "runtime_profile_and_report_card_coverage",
    "benchmark_manifest_floor",
    "source_mix_fixture_and_rp6_evidence",
    "repeat_and_machine_statistics",
    "human_review_scaffold",
    "human_review_handoff_gate",
    "artifact_release_hygiene",
    "safe_real_run_promotion_decisions",
    "claim_ledger_and_boundary_validation",
}
EXPECTED_OPEN_DEPENDENCIES = {
    "two_reviewer_manual_adjudication",
    "final_selected_venue_policy_refresh",
}
FORBIDDEN_CLAIM_KEYS = (
    "paper_grade_completion_claimed",
    "completed_human_review_claimed",
    "reviewer_agreement_claimed",
    "adjudication_claimed",
    "mcnemar_claimed",
    "final_venue_policy_frozen_claimed",
    "external_submission_claimed",
    "public_release_claimed",
    "commercial_runtime_behavior_claimed",
    "public_network_behavior_claimed",
    "defense_success_claimed",
    "source_mix_evidence_completion_claimed",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def repo_path(ref: str) -> Path:
    return REPO_ROOT / ref.split("#", 1)[0]


def validate_refs(refs: list[Any], owner: str) -> None:
    require(refs, f"{owner}: refs must be non-empty")
    for ref in refs:
        require(isinstance(ref, str), f"{owner}: ref must be a string")
        require(repo_path(ref).exists(), f"{owner}: missing ref {ref}")


def validate_completed_gates(status: dict[str, Any]) -> None:
    gates = status.get("completed_non_human_gates")
    require(isinstance(gates, list), "completed_non_human_gates must be a list")
    gates_by_id = {gate.get("gate_id"): gate for gate in gates if isinstance(gate, dict)}
    require(set(gates_by_id) == EXPECTED_COMPLETED_GATES, "completed gate IDs mismatch")
    for gate_id, gate in gates_by_id.items():
        require(str(gate.get("status", "")).startswith("complete_"), f"{gate_id}: status must be complete")
        validate_refs(gate.get("evidence_refs"), gate_id)
        validate_refs(gate.get("validator_refs"), gate_id)


def validate_cross_artifacts(status: dict[str, Any]) -> None:
    scale_gap = load_json(REPO_ROOT / "results" / "derived" / "benchmark-scale-gap.json")
    current = scale_gap["current"]
    full_target = scale_gap["targets"]["full_paper_40_120"]
    require(current["unique_skill_count"] == 44, "benchmark skill count changed")
    require(current["unique_skill_task_contract_triple_count"] == 132, "benchmark triple count changed")
    require(full_target["skill_shortfall"] == 0, "skill shortfall must remain zero")
    require(full_target["triple_shortfall"] == 0, "triple shortfall must remain zero")

    intervals = load_json(REPO_ROOT / "results" / "derived" / "gate5-statistical-intervals.json")
    interval_aggregate = intervals["aggregate"]
    require(interval_aggregate["completed_human_review_count"] == 0, "human review count must remain zero")
    require(interval_aggregate["reviewer_agreement_result_count"] == 0, "reviewer agreement count must remain zero")
    require(interval_aggregate["mcnemar_result_count"] == 0, "McNemar result count must remain zero")
    require(interval_aggregate["wilson_interval_count"] == 36, "Wilson interval count changed")
    require(interval_aggregate["case_bootstrap_interval_count"] == 18, "case bootstrap interval count changed")
    require(interval_aggregate["hierarchical_bootstrap_interval_count"] == 6, "hierarchical interval count changed")

    templates = load_json(REPO_ROOT / "benchmark" / "review" / "gate5-review-export-templates.json")
    template_aggregate = templates["aggregate"]
    require(template_aggregate["template_count"] == 2, "review template count changed")
    require(template_aggregate["assigned_pair_review_unit_count_per_template"] == 122, "assigned pair-review count changed")
    require(template_aggregate["completed_review_export_count"] == 0, "completed review export count must remain zero")
    require(template_aggregate["human_reviewer_identity_count"] == 0, "human reviewer identity count must remain zero")
    require(template_aggregate["agreement_metric_count"] == 0, "agreement metric count must remain zero")
    require(template_aggregate["adjudication_record_count"] == 0, "adjudication record count must remain zero")

    handoff = load_json(REPO_ROOT / "docs" / "research" / "gate5-human-review-handoff.json")
    require(handoff["status"] == "human_review_handoff_ready_no_completed_reviews", "human review handoff status mismatch")
    require(handoff["aggregate"]["template_count"] == 2, "human review handoff template count changed")
    require(handoff["aggregate"]["assigned_pair_review_unit_count_per_template"] == 122, "human review handoff review-unit count changed")
    require(handoff["aggregate"]["completed_review_export_count"] == 0, "human review handoff cannot claim completed exports")
    require(handoff["claim_boundary"]["completed_human_review_claimed"] is False, "human review handoff cannot claim completed review")

    selected_policy = load_json(REPO_ROOT / "docs" / "artifact" / "selected-venue-policy.json")
    require(selected_policy["snapshot"]["requires_refresh_before_submission"] is True, "venue refresh must remain required")
    require(selected_policy["snapshot"]["final_submission_policy_check_complete"] is False, "final venue refresh cannot be complete")
    require(selected_policy["claim_boundary"]["actual_external_submission_claimed"] is False, "external submission cannot be claimed")
    source_audit = load_json(REPO_ROOT / "docs" / "artifact" / "selected-venue-policy-source-audit.json")
    require(source_audit["status"] == "official_source_audit_ready_final_freeze_open", "venue source audit status mismatch")
    require(source_audit["source_count"] == 7, "venue source audit source count mismatch")
    require(
        source_audit["submission_readiness_effect"]["can_close_final_selected_venue_policy_refresh_dependency"] is False,
        "venue source audit cannot close final venue dependency",
    )

    safe_real_run = load_json(REPO_ROOT / "docs" / "research" / "safe-real-run-promotion-decisions.json")
    require(len(safe_real_run["allowed_existing_slices"]) == 2, "safe real-run allowed slice count changed")
    require(len(safe_real_run["blocked_candidates"]) == 5, "safe real-run blocked candidate count changed")
    require(safe_real_run["claim_boundary"]["runtime_drift_claims_added"] is False, "safe real-run cannot add drift claims")

    completion = status.get("completion_state")
    require(isinstance(completion, dict), "completion_state must be an object")
    require(
        completion.get("bounded_non_human_artifacts_complete_for_current_claim_boundary") is True,
        "bounded non-human completion flag must be true",
    )
    require(completion.get("paper_grade_submission_ready") is False, "paper-grade submission readiness cannot be claimed")
    require(completion.get("human_review_completion_percent") == 0, "human review percent must remain zero")
    require(completion.get("final_selected_venue_policy_refresh_complete") is False, "final venue refresh cannot be complete")
    require(
        completion.get("new_safe_real_run_adapters_required_for_current_bounded_state") is False,
        "new adapters must stay optional for current bounded state",
    )


def validate_open_dependencies(status: dict[str, Any]) -> None:
    dependencies = status.get("open_dependencies")
    require(isinstance(dependencies, list), "open_dependencies must be a list")
    dependencies_by_id = {dep.get("dependency_id"): dep for dep in dependencies if isinstance(dep, dict)}
    require(set(dependencies_by_id) == EXPECTED_OPEN_DEPENDENCIES, "open dependency IDs mismatch")
    for dep_id, dep in dependencies_by_id.items():
        require(str(dep.get("status", "")).startswith("open_"), f"{dep_id}: status must be open")
        validate_refs(dep.get("evidence_refs"), dep_id)

    review_counts = dependencies_by_id["two_reviewer_manual_adjudication"]["current_counts"]
    for key in (
        "completed_review_exports",
        "human_reviewer_identities_claimed",
        "reviewer_agreement_metrics",
        "adjudication_records",
    ):
        require(review_counts.get(key) == 0, f"manual review count must remain zero: {key}")

    venue_dep = dependencies_by_id["final_selected_venue_policy_refresh"]
    require(venue_dep.get("selected_venue_id") == "usenix_security_2027_cycle_2", "selected venue mismatch")
    require(venue_dep.get("requires_refresh_before_submission") is True, "final venue refresh must be required")
    require(
        venue_dep.get("current_source_audit_ref") == "docs/artifact/selected-venue-policy-source-audit.json",
        "venue dependency source audit ref mismatch",
    )
    require(
        "docs/artifact/selected-venue-policy-source-audit.json" in venue_dep.get("evidence_refs", []),
        "venue dependency missing source audit evidence",
    )


def validate_optional_work(status: dict[str, Any]) -> None:
    optional = status.get("optional_next_work")
    require(isinstance(optional, list) and len(optional) == 1, "optional_next_work must contain one item")
    item = optional[0]
    require(item.get("work_id") == "new_safe_real_run_adapters", "optional work ID mismatch")
    require(item.get("status") == "optional_not_blocking_current_bounded_non_human_state", "optional adapter status mismatch")
    require(item.get("allowed_existing_slice_count") == 2, "optional allowed slice count mismatch")
    require(item.get("blocked_candidate_count") == 5, "optional blocked candidate count mismatch")
    validate_refs([item.get("decision_ref")], "optional safe real-run adapters")


def validate_claim_boundary(status: dict[str, Any]) -> None:
    boundary = status.get("claim_boundary")
    require(isinstance(boundary, dict), "claim_boundary must be an object")
    for key in FORBIDDEN_CLAIM_KEYS:
        require(boundary.get(key) is False, f"claim boundary must remain false: {key}")


def validate_docs() -> None:
    status_doc = STATUS_DOC_PATH.read_text(encoding="utf-8")
    for required in (
        "Status: bounded non-human artifacts ready for the current claim boundary",
        "Two independent real human reviewers",
        "selected-venue policy source audit",
        "final official CFP/CFA",
        "python3 tools/validate_submission_readiness_status.py",
    ):
        require(required in status_doc, f"status doc missing: {required}")

    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    require("submission-readiness status" in roadmap, "roadmap must mention submission-readiness status")
    require("human/manual adjudication" in roadmap, "roadmap must keep human-review blocker")
    require("final selected-venue policy refresh" in roadmap, "roadmap must keep final venue refresh blocker")

    todo = TODO_PATH.read_text(encoding="utf-8")
    require("bounded non-human evidence boundary" in todo, "TODO must keep bounded non-human boundary")
    require("selective real-run promotion decisions" not in todo, "TODO still has stale safe real-run blocker text")

    readme = README_PATH.read_text(encoding="utf-8")
    require("Submission readiness status" in readme, "README must point to readiness status")
    require("human review 0%" in readme, "README must preserve human review 0%")

    verify_script = VERIFY_SCRIPT_PATH.read_text(encoding="utf-8")
    require("tools/validate_submission_readiness_status.py" in verify_script, "verify_all must run readiness validator")


def main() -> int:
    status = load_json(STATUS_PATH)
    require(isinstance(status, dict), "submission-readiness status must be an object")
    require(status.get("schema_version") == "0.1", "submission-readiness schema mismatch")
    require(status.get("status") == EXPECTED_STATUS, "submission-readiness status mismatch")
    require(status.get("checked_on") == EXPECTED_DATE, "submission-readiness date mismatch")
    require(status.get("timezone") == "Asia/Kolkata", "submission-readiness timezone mismatch")
    validate_completed_gates(status)
    validate_cross_artifacts(status)
    validate_open_dependencies(status)
    validate_optional_work(status)
    validate_claim_boundary(status)
    validate_docs()
    print("validated submission-readiness status")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"submission-readiness validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
