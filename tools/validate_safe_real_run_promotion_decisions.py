#!/usr/bin/env python3
"""Validate safe real-run promotion decisions and claim boundaries."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DECISION_PATH = REPO_ROOT / "docs" / "research" / "safe-real-run-promotion-decisions.json"
DECISION_DOC_PATH = REPO_ROOT / "docs" / "research" / "safe-real-run-promotion-decisions.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "research" / "research-roadmap.md"
TODO_PATH = REPO_ROOT / "docs" / "research" / "research-todo.md"
METHOD_BOUNDARIES_PATH = REPO_ROOT / "paper" / "method-boundaries.md"
EVIDENCE_MATRIX_PATH = REPO_ROOT / "paper" / "tables" / "evidence-boundary-matrix.md"
VERIFY_SCRIPT_PATH = REPO_ROOT / "scripts" / "verify_all.sh"

EXPECTED_STATUS = "safe_real_run_promotion_decisions_ready_no_new_live_execution"
EXPECTED_DATE = "2026-06-01"
EXPECTED_ALLOWED_DECISIONS = {
    "docs-forge-bounded-local-live-slices",
    "ripgrep-public-live-local-binary",
}
EXPECTED_BLOCKED_CANDIDATES = {
    "audit-lens-full-product-or-live-connector",
    "external-mcp-server-or-connector-auth",
    "public-registry-package-acquisition",
    "credentialed-api-or-webhook-workflow",
    "commercial-hosted-or-plugin-store-runtime",
}
FORBIDDEN_CLAIM_KEYS = (
    "new_live_execution_claimed",
    "public_network_execution_claimed",
    "real_credentials_used_claimed",
    "commercial_runtime_behavior_claimed",
    "full_product_behavior_claimed",
    "runtime_drift_claims_added",
    "defense_success_claimed",
    "human_review_completed_claimed",
)
REQUIRED_BLOCKED_CLAIMS = {
    "public_network_behavior",
    "commercial_runtime_behavior",
    "defense_success",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def repo_path(ref: str) -> Path:
    return REPO_ROOT / ref.split("#", 1)[0]


def aggregate_zero_or_absent(result: dict[str, Any], key: str, ref: str) -> None:
    aggregate = result.get("aggregate", {})
    require(isinstance(aggregate, dict), f"{ref}: aggregate must be an object")
    if key in aggregate:
        require(aggregate[key] == 0, f"{ref}: aggregate.{key} must be zero")


def aggregate_false_or_absent(result: dict[str, Any], key: str, ref: str) -> None:
    aggregate = result.get("aggregate", {})
    require(isinstance(aggregate, dict), f"{ref}: aggregate must be an object")
    if key in aggregate:
        require(aggregate[key] is False, f"{ref}: aggregate.{key} must be false")


def validate_result_ref(ref: str) -> dict[str, Any]:
    path = repo_path(ref)
    require(path.is_file(), f"missing result ref: {ref}")
    result = load_json(path)
    require(isinstance(result, dict), f"{ref}: result must be an object")
    require(result.get("schema_version") == "0.1", f"{ref}: schema mismatch")
    require(result.get("safe_to_publish") is True, f"{ref}: safe_to_publish must be true")
    require(result.get("real_secrets_present") is False, f"{ref}: real_secrets_present must be false")
    require(
        result.get("excluded_from_mvp_runtime_counts") is True,
        f"{ref}: result must remain excluded from MVP runtime counts",
    )
    aggregate_zero_or_absent(result, "runtime_drift_claims_added", ref)
    aggregate_zero_or_absent(result, "pairwise_disagreements_added", ref)
    aggregate_zero_or_absent(result, "canonical_traces_added", ref)
    aggregate_zero_or_absent(result, "canonical_results_added", ref)
    aggregate_zero_or_absent(result, "public_registry_acquisitions_observed", ref)
    aggregate_false_or_absent(result, "runtime_drift_counts_changed", ref)
    aggregate_false_or_absent(result, "public_internet_contact_observed", ref)
    return result


def validate_manifest_ref(ref: str) -> None:
    path = repo_path(ref)
    require(path.is_file(), f"missing manifest ref: {ref}")
    manifest = load_json(path)
    require(manifest.get("safe_to_publish") is True, f"{ref}: manifest safe_to_publish must be true")
    require(manifest.get("real_secrets_present") is False, f"{ref}: manifest real_secrets_present must be false")
    require(manifest.get("excluded_from_mvp_runtime_counts") is True, f"{ref}: manifest must stay excluded")
    binary_boundary = manifest.get("binary_boundary", {})
    if isinstance(binary_boundary, dict) and "public_network_execution" in binary_boundary:
        require(binary_boundary["public_network_execution"] is False, f"{ref}: public network execution must be false")


def validate_decision(policy: dict[str, Any]) -> None:
    require(policy.get("schema_version") == "0.1", "decision schema mismatch")
    require(policy.get("status") == EXPECTED_STATUS, "decision status mismatch")
    require(policy.get("decided_on") == EXPECTED_DATE, "decision date mismatch")
    require(policy.get("timezone") == "Asia/Kolkata", "decision timezone mismatch")

    guardrails = policy.get("global_guardrails")
    require(isinstance(guardrails, dict), "global_guardrails must be an object")
    for key, value in guardrails.items():
        require(value is False, f"global guardrail must be false: {key}")

    allowed = policy.get("allowed_existing_slices")
    require(isinstance(allowed, list), "allowed_existing_slices must be a list")
    allowed_by_id = {item.get("decision_id"): item for item in allowed if isinstance(item, dict)}
    require(set(allowed_by_id) == EXPECTED_ALLOWED_DECISIONS, "allowed decision IDs mismatch")

    for decision_id, item in allowed_by_id.items():
        require(item.get("decision", "").startswith("already_promoted_"), f"{decision_id}: decision mismatch")
        blocked_claims = set(item.get("blocked_claims", []))
        require(REQUIRED_BLOCKED_CLAIMS.issubset(blocked_claims), f"{decision_id}: missing blocked claims")
        result_refs = item.get("result_refs")
        require(isinstance(result_refs, list) and result_refs, f"{decision_id}: result_refs must be non-empty")
        for ref in result_refs:
            require(isinstance(ref, str), f"{decision_id}: result ref must be a string")
            validate_result_ref(ref)
        manifest_ref = item.get("manifest_ref")
        if manifest_ref is not None:
            require(isinstance(manifest_ref, str), f"{decision_id}: manifest_ref must be a string")
            validate_manifest_ref(manifest_ref)

    blocked = policy.get("blocked_candidates")
    require(isinstance(blocked, list), "blocked_candidates must be a list")
    blocked_by_id = {item.get("candidate_id"): item for item in blocked if isinstance(item, dict)}
    require(set(blocked_by_id) == EXPECTED_BLOCKED_CANDIDATES, "blocked candidate IDs mismatch")
    for candidate_id, item in blocked_by_id.items():
        require(item.get("decision") == "blocked_no_safe_current_execution", f"{candidate_id}: blocked decision mismatch")
        require(item.get("blocked_reason"), f"{candidate_id}: missing blocked reason")
        require(item.get("allowed_next_step"), f"{candidate_id}: missing allowed next step")
        protocol = item.get("required_protocol_before_promotion")
        require(isinstance(protocol, list) and "claim_ledger_update" in protocol, f"{candidate_id}: protocol must require claim ledger update")

    boundary = policy.get("claim_boundary")
    require(isinstance(boundary, dict), "claim_boundary must be an object")
    for key in FORBIDDEN_CLAIM_KEYS:
        require(boundary.get(key) is False, f"claim boundary must remain false: {key}")


def validate_docs() -> None:
    decision_doc = DECISION_DOC_PATH.read_text(encoding="utf-8")
    for required in (
        "Status: decision gate for existing bounded evidence; no new live execution.",
        "docs-forge-bounded-local-live-slices",
        "ripgrep-public-live-local-binary",
        "python3 tools/validate_safe_real_run_promotion_decisions.py",
        "No public-network, credentialed, commercial-runtime, full-product,",
    ):
        require(required in decision_doc, f"decision doc missing: {required}")

    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    require("safe real-run promotion decision gate" in roadmap, "roadmap must mention safe real-run gate")
    require("new safe real-run adapters remain optional" in roadmap, "roadmap must preserve optional-adapter boundary")

    todo = TODO_PATH.read_text(encoding="utf-8")
    require(
        "safe real-run promotion decision" in todo and "gate" in todo,
        "TODO must mention safe real-run gate",
    )
    require("human-reviewed" in todo, "TODO must keep human-review blocker")

    method = METHOD_BOUNDARIES_PATH.read_text(encoding="utf-8")
    require("Safe real-run promotion decision gate" in method, "method boundaries must include safe real-run gate row")

    matrix = EVIDENCE_MATRIX_PATH.read_text(encoding="utf-8")
    require("| Safe real-run promotion decisions | Promoted bounded evidence |" in matrix, "evidence matrix must include safe real-run row")

    verify_script = VERIFY_SCRIPT_PATH.read_text(encoding="utf-8")
    require("tools/validate_safe_real_run_promotion_decisions.py" in verify_script, "verify_all must run safe real-run validator")


def main() -> int:
    policy = load_json(DECISION_PATH)
    require(isinstance(policy, dict), "decision manifest must parse as an object")
    validate_decision(policy)
    validate_docs()
    print("validated safe real-run promotion decisions")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"safe real-run promotion validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
