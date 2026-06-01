#!/usr/bin/env python3
"""Validate Gate 5 human-review handoff readiness without claiming review completion."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
HANDOFF_PATH = REPO_ROOT / "docs" / "research" / "gate5-human-review-handoff.json"
HANDOFF_DOC_PATH = REPO_ROOT / "docs" / "research" / "gate5-human-review-handoff.md"
SUBMISSION_STATUS_PATH = REPO_ROOT / "docs" / "research" / "submission-readiness-status.json"
README_PATH = REPO_ROOT / "README.md"
TODO_PATH = REPO_ROOT / "docs" / "research" / "research-todo.md"
VERIFY_SCRIPT_PATH = REPO_ROOT / "scripts" / "verify_all.sh"

EXPECTED_STATUS = "human_review_handoff_ready_no_completed_reviews"
EXPECTED_DATE = "2026-06-01"
EXPECTED_REFS = {
    "review_queue": "benchmark/review/gate5-review-queue.json",
    "review_packet_index": "benchmark/review/gate5-review-packet-index.json",
    "blinded_packet_bundle": "benchmark/review/gate5-blinded-packet-bundle.json",
    "review_export_templates": "benchmark/review/gate5-review-export-templates.json",
    "completed_review_schema": "schemas/gate5_completed_review_export.schema.json",
    "completed_review_validator": "tools/validate_gate5_completed_review_export.py",
    "adjudication_form": "paper/gate5-adjudication-form.md",
}
EXPECTED_REVIEWER_SLOTS = {
    "reviewer_a": "gate5-reviewer_a-first-pass-template",
    "reviewer_b": "gate5-reviewer_b-first-pass-template",
}
FORBIDDEN_CLAIM_KEYS = (
    "completed_human_review_claimed",
    "human_reviewer_identity_claimed",
    "reviewer_agreement_claimed",
    "adjudication_claimed",
    "completed_statistics_claimed",
    "mcnemar_claimed",
    "prevalence_claim",
    "paper_grade_completion_claimed",
    "codex_assisted_review_counted_as_human",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def repo_path(ref: str) -> Path:
    return REPO_ROOT / ref.split("#", 1)[0]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_refs(handoff: dict[str, Any]) -> None:
    refs = handoff.get("handoff_refs")
    require(isinstance(refs, dict), "handoff_refs must be an object")
    require(refs == EXPECTED_REFS, "handoff refs mismatch")
    for key, ref in refs.items():
        require(repo_path(ref).is_file(), f"missing handoff ref {key}: {ref}")


def validate_aggregate(handoff: dict[str, Any]) -> None:
    refs = handoff["handoff_refs"]
    queue = load_json(repo_path(refs["review_queue"]))
    bundle = load_json(repo_path(refs["blinded_packet_bundle"]))
    templates = load_json(repo_path(refs["review_export_templates"]))

    queue_agg = queue["aggregate"]
    bundle_agg = bundle["aggregate"]
    template_agg = templates["aggregate"]
    aggregate = handoff.get("aggregate")
    require(isinstance(aggregate, dict), "aggregate must be an object")

    expected = {
        "queued_item_count": queue_agg["queued_item_count"],
        "source_packet_count": template_agg["source_packet_count"],
        "blinding_eligible_item_count": queue_agg["blinding_eligible_item_count"],
        "exported_blinded_packet_count": bundle_agg["exported_packet_count"],
        "blocked_metadata_only_packet_count": template_agg["blocked_packet_count"],
        "template_count": template_agg["template_count"],
        "assigned_pair_review_unit_count_per_template": template_agg["assigned_pair_review_unit_count_per_template"],
        "completed_review_export_count": template_agg["completed_review_export_count"],
        "human_reviewer_identity_count": template_agg["human_reviewer_identity_count"],
        "agreement_metric_count": template_agg["agreement_metric_count"],
        "adjudication_record_count": template_agg["adjudication_record_count"],
    }
    require(aggregate == expected, "handoff aggregate does not match source artifacts")
    require(aggregate["queued_item_count"] == 132, "queued item count changed")
    require(aggregate["exported_blinded_packet_count"] == 122, "exported blinded packet count changed")
    require(aggregate["blocked_metadata_only_packet_count"] == 10, "blocked packet count changed")
    for key in (
        "completed_review_export_count",
        "human_reviewer_identity_count",
        "agreement_metric_count",
        "adjudication_record_count",
    ):
        require(aggregate[key] == 0, f"{key} must remain zero")

    lock = handoff.get("handoff_lock")
    require(isinstance(lock, dict), "handoff_lock must be an object")
    require(
        lock.get("review_export_templates_sha256") == sha256_file(repo_path(refs["review_export_templates"])),
        "review export template hash mismatch",
    )
    require(
        lock.get("blinded_packet_bundle_sha256") == sha256_file(repo_path(refs["blinded_packet_bundle"])),
        "blinded packet bundle hash mismatch",
    )


def validate_reviewer_slots(handoff: dict[str, Any]) -> None:
    refs = handoff["handoff_refs"]
    templates = load_json(repo_path(refs["review_export_templates"]))
    template_by_slot = {
        template["assignment"]["reviewer_slot"]: template
        for template in templates["templates"]
    }
    slots = handoff.get("reviewer_slots")
    require(isinstance(slots, list) and len(slots) == 2, "reviewer_slots must contain two entries")
    slots_by_id = {slot.get("reviewer_slot"): slot for slot in slots if isinstance(slot, dict)}
    require(set(slots_by_id) == set(EXPECTED_REVIEWER_SLOTS), "reviewer slot IDs mismatch")
    for slot_id, expected_template_id in EXPECTED_REVIEWER_SLOTS.items():
        slot = slots_by_id[slot_id]
        template = template_by_slot[slot_id]
        require(slot.get("template_export_id") == expected_template_id, f"{slot_id}: template ID mismatch")
        require(slot["template_export_id"] == template["export_id"], f"{slot_id}: source template mismatch")
        require(slot.get("assigned_pair_review_units") == len(template["review_items"]), f"{slot_id}: item count mismatch")
        require(slot.get("assigned_pair_review_units") == 122, f"{slot_id}: expected 122 review units")
        require(slot.get("required_completed_export_kind") == "completed_human_review_export", f"{slot_id}: export kind mismatch")
        require(template["assignment"]["counts_as_human_review"] is False, f"{slot_id}: blank template cannot count as review")


def validate_boundaries(handoff: dict[str, Any]) -> None:
    requirements = handoff.get("human_reviewer_requirements")
    require(isinstance(requirements, list) and len(requirements) >= 6, "reviewer requirements are incomplete")
    requirements_text = "\n".join(requirements)
    for required in (
        "two independent real human reviewers",
        "Codex-assisted",
        "Complete every assigned pair-review unit",
        "Do not compute reviewer agreement",
    ):
        require(required in requirements_text, f"reviewer requirements missing: {required}")

    commands = handoff.get("validation_commands")
    require(isinstance(commands, list), "validation_commands must be a list")
    require(
        "python3 tools/validate_gate5_completed_review_export.py <completed-review-export.json>" in commands,
        "completed export validator command missing",
    )
    require("python3 tools/validate_gate5_human_review_handoff.py" in commands, "handoff validator command missing")

    blocked = set(handoff.get("blocked_until_completed_exports", []))
    require(
        {
            "reviewer_agreement_claims",
            "cohens_kappa_claims",
            "adjudication_claims",
            "human_reviewed_statistics",
            "paper_grade_submission_readiness",
        }.issubset(blocked),
        "blocked-until-completed list incomplete",
    )

    boundary = handoff.get("claim_boundary")
    require(isinstance(boundary, dict), "claim_boundary must be an object")
    for key in FORBIDDEN_CLAIM_KEYS:
        require(boundary.get(key) is False, f"claim boundary must remain false: {key}")


def validate_docs() -> None:
    handoff_doc = HANDOFF_DOC_PATH.read_text(encoding="utf-8")
    for required in (
        "Status: handoff package ready; no completed human review.",
        "python3 tools/validate_gate5_completed_review_export.py <completed-review-export.json>",
        "python3 tools/validate_gate5_human_review_handoff.py",
        "Codex-assisted, synthetic, anonymous, placeholder, fake, dummy, or test",
    ):
        require(required in handoff_doc, f"handoff doc missing: {required}")

    status = load_json(SUBMISSION_STATUS_PATH)
    gate_ids = {
        gate.get("gate_id")
        for gate in status.get("completed_non_human_gates", [])
        if isinstance(gate, dict)
    }
    require("human_review_handoff_gate" in gate_ids, "submission-readiness status missing handoff gate")
    require(
        status["completion_state"]["human_review_completion_percent"] == 0,
        "submission readiness must keep human review at 0%",
    )
    require(status["claim_boundary"]["completed_human_review_claimed"] is False, "submission status cannot claim human review")

    readme = README_PATH.read_text(encoding="utf-8")
    require("Gate 5 human-review handoff" in readme, "README must point to human-review handoff")

    todo = TODO_PATH.read_text(encoding="utf-8")
    require("human-review handoff gate" in todo, "TODO must mention human-review handoff gate")

    verify_script = VERIFY_SCRIPT_PATH.read_text(encoding="utf-8")
    require("tools/validate_gate5_human_review_handoff.py" in verify_script, "verify_all must run handoff validator")


def main() -> int:
    handoff = load_json(HANDOFF_PATH)
    require(isinstance(handoff, dict), "handoff manifest must be an object")
    require(handoff.get("schema_version") == "0.1", "handoff schema mismatch")
    require(handoff.get("status") == EXPECTED_STATUS, "handoff status mismatch")
    require(handoff.get("checked_on") == EXPECTED_DATE, "handoff date mismatch")
    require(handoff.get("timezone") == "Asia/Kolkata", "handoff timezone mismatch")
    validate_refs(handoff)
    validate_aggregate(handoff)
    validate_reviewer_slots(handoff)
    validate_boundaries(handoff)
    validate_docs()
    print("validated Gate 5 human-review handoff")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Gate 5 human-review handoff validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
