#!/usr/bin/env python3
"""Validate selected-venue official-source audit boundaries."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = REPO_ROOT / "docs" / "artifact" / "selected-venue-policy-source-audit.json"
AUDIT_DOC_PATH = REPO_ROOT / "docs" / "artifact" / "selected-venue-policy-source-audit.md"
POLICY_PATH = REPO_ROOT / "docs" / "artifact" / "selected-venue-policy.json"
SUBMISSION_STATUS_PATH = REPO_ROOT / "docs" / "research" / "submission-readiness-status.json"
VERIFY_SCRIPT_PATH = REPO_ROOT / "scripts" / "verify_all.sh"

EXPECTED_STATUS = "official_source_audit_ready_final_freeze_open"
EXPECTED_CHECKED_ON = "2026-06-01"
EXPECTED_TIMEZONE = "Asia/Kolkata"
SELECTED_VENUE_ID = "usenix_security_2027_cycle_2"
EXPECTED_SOURCE_IDS = {
    "usenix_security_2027_dates",
    "usenix_security_2026_cfp_precedent",
    "usenix_security_2026_cfa_precedent",
    "ndss_2027_cfp",
    "ndss_2027_cfa",
    "ieee_sp_2027_cfp",
    "acm_ccs_2026_cfp",
}
EXPECTED_BOUNDARY_FALSE_KEYS = (
    "final_submission_policy_check_complete",
    "final_cfp_policy_frozen_claimed",
    "external_submission_claimed",
    "anonymous_artifact_access_finalized",
    "ai_use_wording_finalized",
    "public_release_claimed",
    "completed_human_review_claimed",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_sources(audit: dict[str, Any]) -> None:
    sources = audit.get("official_sources")
    require(isinstance(sources, list), "official_sources must be a list")
    require(len(sources) == audit.get("source_count") == 7, "source count mismatch")
    require(audit.get("official_source_count") == 7, "official source count mismatch")
    sources_by_id = {source.get("source_id"): source for source in sources if isinstance(source, dict)}
    require(set(sources_by_id) == EXPECTED_SOURCE_IDS, "official source ID set mismatch")

    for source_id, source in sources_by_id.items():
        require(source.get("source_kind", "").startswith("official"), f"{source_id}: non-official source kind")
        url = source.get("url")
        require(isinstance(url, str) and url.startswith("https://"), f"{source_id}: source URL must be HTTPS")
        require("example." not in url and "localhost" not in url, f"{source_id}: placeholder URL")
        facts = source.get("facts_verified")
        require(isinstance(facts, list) and facts, f"{source_id}: facts_verified must be non-empty")
        require(isinstance(source.get("use_in_selected_policy"), str), f"{source_id}: use boundary missing")

    usenix_2027 = sources_by_id["usenix_security_2027_dates"]
    facts = set(usenix_2027["facts_verified"])
    require("cycle_2_submission_deadline_2027-01-26" in facts, "USENIX Cycle 2 submission deadline missing")
    require("detailed_2027_cfp_cfa_not_available_in_tracked_source_set" in facts, "USENIX detailed-policy boundary missing")

    usenix_2026_cfp = sources_by_id["usenix_security_2026_cfp_precedent"]
    require(
        usenix_2026_cfp.get("use_in_selected_policy") == "official_precedent_only_until_2027_detailed_cfp_available",
        "USENIX 2026 CFP must be precedent-only",
    )
    usenix_2026_cfa = sources_by_id["usenix_security_2026_cfa_precedent"]
    require(
        usenix_2026_cfa.get("use_in_selected_policy") == "official_precedent_only_until_2027_detailed_cfa_available",
        "USENIX 2026 CFA must be precedent-only",
    )


def validate_selected_target(audit: dict[str, Any]) -> None:
    selected = audit.get("selected_target_refresh_result")
    require(isinstance(selected, dict), "selected_target_refresh_result must be an object")
    require(selected.get("venue_id") == SELECTED_VENUE_ID, "selected target venue mismatch")
    require(selected.get("current_official_dates_available") is True, "USENIX 2027 dates must be available")
    require(selected.get("registration_deadline") == "2027-01-19", "registration deadline mismatch")
    require(selected.get("paper_submission_deadline") == "2027-01-26", "submission deadline mismatch")
    require(selected.get("conference_dates") == {"start": "2027-08-11", "end": "2027-08-13"}, "conference dates mismatch")
    require(selected.get("detailed_2027_cfp_available") is False, "detailed 2027 CFP cannot be claimed")
    require(selected.get("detailed_2027_cfa_available") is False, "detailed 2027 CFA cannot be claimed")
    require(selected.get("uses_2026_policy_as_precedent_only") is True, "2026 policy must stay precedent-only")
    require(selected.get("final_refresh_required_before_external_submission") is True, "final refresh must remain required")

    readiness = audit.get("submission_readiness_effect")
    require(isinstance(readiness, dict), "submission_readiness_effect must be an object")
    require(readiness.get("can_update_selected_venue_snapshot") is True, "snapshot update readiness mismatch")
    require(
        readiness.get("can_close_final_selected_venue_policy_refresh_dependency") is False,
        "final venue dependency cannot be closed by this audit",
    )
    require(readiness.get("paper_grade_submission_ready") is False, "paper-grade readiness cannot be claimed")
    require("detailed 2027 CFP/CFA remains unavailable" in readiness.get("reason_dependency_stays_open", ""), "dependency boundary reason missing")


def validate_boundaries(audit: dict[str, Any]) -> None:
    boundary = audit.get("claim_boundary")
    require(isinstance(boundary, dict), "claim_boundary must be an object")
    require(boundary.get("official_source_refresh_recorded") is True, "official-source refresh must be recorded")
    for key in EXPECTED_BOUNDARY_FALSE_KEYS:
        require(boundary.get(key) is False, f"claim boundary must remain false: {key}")


def validate_cross_artifacts(audit: dict[str, Any]) -> None:
    policy = load_json(POLICY_PATH)
    require(policy.get("source_audit_ref") == "docs/artifact/selected-venue-policy-source-audit.json", "selected policy missing source audit ref")
    require(policy["snapshot"]["final_submission_policy_check_complete"] is False, "selected policy cannot claim final check")
    require(policy["snapshot"]["requires_refresh_before_submission"] is True, "selected policy must require refresh")
    require(policy["selected_target_requirements"]["paper_submission_deadline"] == "2027-01-26", "selected policy deadline mismatch")

    policy_source_ids = {source["source_id"] for source in policy["policy_sources"]}
    audit_source_ids = {source["source_id"] for source in audit["official_sources"]}
    require(policy_source_ids == audit_source_ids, "selected policy source IDs must match audit")

    status = load_json(SUBMISSION_STATUS_PATH)
    require(status["completion_state"]["final_selected_venue_policy_refresh_complete"] is False, "submission status cannot close final venue refresh")
    dependencies = {
        dependency["dependency_id"]: dependency
        for dependency in status.get("open_dependencies", [])
        if isinstance(dependency, dict)
    }
    venue_dependency = dependencies.get("final_selected_venue_policy_refresh")
    require(isinstance(venue_dependency, dict), "submission status missing final venue dependency")
    require(
        "docs/artifact/selected-venue-policy-source-audit.json" in venue_dependency.get("evidence_refs", []),
        "submission status venue dependency missing source audit ref",
    )
    require(
        venue_dependency.get("current_source_audit_ref") == "docs/artifact/selected-venue-policy-source-audit.json",
        "submission status source audit ref mismatch",
    )

    verify_script = VERIFY_SCRIPT_PATH.read_text(encoding="utf-8")
    require(
        "tools/validate_selected_venue_policy_source_audit.py" in verify_script,
        "verify_all must run selected venue source audit validator",
    )


def validate_doc() -> None:
    text = AUDIT_DOC_PATH.read_text(encoding="utf-8")
    for required in (
        "Status: official-source audit recorded; final venue-policy freeze still open.",
        "usenix_security_2027_cycle_2",
        "python3 tools/validate_selected_venue_policy_source_audit.py",
        "It does not close the final selected-venue policy refresh dependency.",
    ):
        require(required in text, f"source audit doc missing: {required}")


def main() -> int:
    audit = load_json(AUDIT_PATH)
    require(isinstance(audit, dict), "source audit must parse as a JSON object")
    require(audit.get("schema_version") == "0.1", "source audit schema mismatch")
    require(audit.get("status") == EXPECTED_STATUS, "source audit status mismatch")
    require(audit.get("checked_on") == EXPECTED_CHECKED_ON, "source audit checked_on mismatch")
    require(audit.get("timezone") == EXPECTED_TIMEZONE, "source audit timezone mismatch")
    require(audit.get("selected_venue_id") == SELECTED_VENUE_ID, "source audit selected venue mismatch")
    require(
        audit.get("source_policy_state") == "usenix_security_2027_dates_official_2026_detailed_policy_precedent",
        "source policy state mismatch",
    )
    validate_sources(audit)
    validate_selected_target(audit)
    validate_boundaries(audit)
    validate_cross_artifacts(audit)
    validate_doc()
    print("validated selected venue policy source audit")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"selected venue policy source audit validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
