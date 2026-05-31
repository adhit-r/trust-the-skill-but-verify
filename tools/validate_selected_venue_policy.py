#!/usr/bin/env python3
"""Validate the selected-venue policy snapshot and packaging boundaries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = REPO_ROOT / "docs" / "artifact" / "selected-venue-policy.json"
POLICY_DOC_PATH = REPO_ROOT / "docs" / "artifact" / "selected-venue-policy.md"
PROFILES_PATH = REPO_ROOT / "docs" / "artifact" / "venue-packaging-profiles.json"
PACKAGING_PASS_PATH = REPO_ROOT / "docs" / "artifact" / "venue-packaging-pass.md"
AI_DISCLOSURE_PATH = REPO_ROOT / "docs" / "artifact" / "ai-use-disclosure.md"
RELEASE_CHECKLIST_PATH = REPO_ROOT / "docs" / "artifact" / "release-checklist.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "research" / "research-roadmap.md"
TODO_PATH = REPO_ROOT / "docs" / "research" / "research-todo.md"
PAPER_SPINE_PATH = REPO_ROOT / "paper" / "paper-spine.md"

EXPECTED_STATUS = "selected_venue_policy_snapshot_ready_no_external_submission"
EXPECTED_CHECKED_ON = "2026-06-01"
EXPECTED_TIMEZONE = "Asia/Kolkata"
SELECTED_VENUE_ID = "usenix_security_2027_cycle_2"
ANONYMOUS_PROFILE = "anonymous_review"
PUBLIC_PROFILE = "public_archive"
OFFICIAL_SOURCE_IDS = {
    "usenix_security_2027_dates",
    "usenix_security_2026_cfp_precedent",
    "usenix_security_2026_cfa_precedent",
    "ndss_2027_cfp",
    "ndss_2027_cfa",
    "ieee_sp_2027_cfp",
    "acm_ccs_2026_cfp",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_policy(policy: dict[str, Any]) -> None:
    require(policy.get("schema_version") == "0.1", "selected venue policy schema mismatch")
    require(policy.get("status") == EXPECTED_STATUS, "selected venue policy status mismatch")

    selected = policy.get("selected_policy_target")
    require(isinstance(selected, dict), "selected_policy_target must be an object")
    require(selected.get("venue_id") == SELECTED_VENUE_ID, "selected venue id mismatch")
    require(selected.get("role") == "primary_realistic_target", "selected venue role mismatch")
    require(
        selected.get("submission_packaging_profile") == ANONYMOUS_PROFILE,
        "selected target must use anonymous_review for external review",
    )
    require(
        selected.get("post_acceptance_packaging_profile") == PUBLIC_PROFILE,
        "selected target must keep public_archive as post-acceptance profile",
    )

    snapshot = policy.get("snapshot")
    require(isinstance(snapshot, dict), "snapshot must be an object")
    require(snapshot.get("checked_on") == EXPECTED_CHECKED_ON, "snapshot checked_on mismatch")
    require(snapshot.get("timezone") == EXPECTED_TIMEZONE, "snapshot timezone mismatch")
    require(
        snapshot.get("source_policy_state")
        == "usenix_security_2027_dates_official_2026_detailed_policy_precedent",
        "snapshot policy state mismatch",
    )
    require(snapshot.get("final_submission_policy_check_complete") is False, "final submission policy cannot be claimed")
    require(snapshot.get("requires_refresh_before_submission") is True, "pre-submission refresh must be required")
    require("2027" in snapshot.get("reason_final_check_open", "") and "CFP/CFA" in snapshot.get("reason_final_check_open", ""), "missing final-check boundary reason")

    sources = policy.get("policy_sources")
    require(isinstance(sources, list), "policy_sources must be a list")
    sources_by_id = {source.get("source_id"): source for source in sources if isinstance(source, dict)}
    require(set(sources_by_id) == OFFICIAL_SOURCE_IDS, "official policy source set mismatch")
    for source_id, source in sources_by_id.items():
        require(source.get("checked_on") == EXPECTED_CHECKED_ON, f"{source_id}: checked_on mismatch")
        require(source.get("source_kind", "").startswith("official"), f"{source_id}: source must be official")
        url = source.get("url")
        require(isinstance(url, str) and url.startswith("https://"), f"{source_id}: official URL missing")
        require("example." not in url and "localhost" not in url, f"{source_id}: placeholder URL")
        facts = source.get("facts_used")
        require(isinstance(facts, list) and facts, f"{source_id}: facts_used must be non-empty")

    requirements = policy.get("selected_target_requirements")
    require(isinstance(requirements, dict), "selected_target_requirements must be an object")
    require(requirements.get("venue_id") == SELECTED_VENUE_ID, "selected requirements venue mismatch")
    require(requirements.get("registration_deadline") == "2027-01-19", "USENIX registration deadline mismatch")
    require(requirements.get("paper_submission_deadline") == "2027-01-26", "USENIX submission deadline mismatch")
    require(requirements.get("paper_review_anonymity_required") is True, "paper anonymity must be required")
    require(
        requirements.get("anonymous_artifact_access_at_submission_required") is True,
        "anonymous artifact access must be required for selected review package",
    )
    require(requirements.get("open_science_appendix_required") is True, "Open Science appendix must be tracked")
    require(
        requirements.get("ethical_considerations_appendix_required") is True,
        "Ethical Considerations appendix must be tracked",
    )
    require(requirements.get("all_authors_orcid_required_by_registration") is True, "ORCID requirement must be tracked")

    ai_policy = requirements.get("ai_use_policy")
    require(isinstance(ai_policy, dict), "ai_use_policy must be an object")
    require(
        ai_policy.get("status") == "venue_specific_manual_finalization_required",
        "AI-use policy must stay manual-finalization gated",
    )
    require(
        ai_policy.get("draft_disclosure_file") == "docs/artifact/ai-use-disclosure.md",
        "AI disclosure draft path mismatch",
    )

    submission = requirements.get("submission_packaging")
    require(isinstance(submission, dict), "submission_packaging must be an object")
    require(submission.get("required_profile") == ANONYMOUS_PROFILE, "selected submission profile mismatch")
    require(submission.get("forbidden_deanonymizing_repository_metadata") is True, "anonymous metadata denylist missing")
    require(submission.get("public_archive_profile_forbidden_in_review_submission") is True, "public archive must be forbidden in review package")
    require(submission.get("actual_hotcrp_submission_claimed") is False, "HotCRP submission cannot be claimed")

    post_acceptance = requirements.get("post_acceptance_artifact_policy")
    require(isinstance(post_acceptance, dict), "post_acceptance_artifact_policy must be an object")
    require(post_acceptance.get("post_acceptance_profile") == PUBLIC_PROFILE, "post-acceptance profile mismatch")
    require(
        post_acceptance.get("continued_availability_verification_required_for_promised_artifacts") is True,
        "continued availability verification must be tracked",
    )
    require(
        post_acceptance.get("github_only_archive_insufficient_for_permanent_availability") is True,
        "GitHub-only archive insufficiency must be tracked",
    )

    backplan = policy.get("candidate_venue_backplan")
    require(isinstance(backplan, list) and len(backplan) == 4, "candidate venue backplan mismatch")
    backplan_by_id = {item.get("venue_id"): item for item in backplan if isinstance(item, dict)}
    require(
        {SELECTED_VENUE_ID, "ndss_2027_fall", "ieee_sp_2027_second_deadline", "acm_ccs_2026_cycle_b"}
        == set(backplan_by_id),
        "candidate venue IDs mismatch",
    )
    require(backplan_by_id["ndss_2027_fall"].get("paper_submission_deadline") == "2026-08-19", "NDSS fall deadline mismatch")
    require(
        backplan_by_id["ieee_sp_2027_second_deadline"].get("paper_submission_deadline") == "2026-11-17",
        "IEEE S&P second deadline mismatch",
    )
    require(
        backplan_by_id[SELECTED_VENUE_ID].get("paper_submission_deadline") == "2027-01-26",
        "USENIX selected deadline mismatch",
    )

    boundary = policy.get("claim_boundary")
    require(isinstance(boundary, dict), "claim_boundary must be an object")
    for key in (
        "actual_external_submission_claimed",
        "accepted_by_venue_claimed",
        "completed_human_review_claimed",
        "public_release_claimed",
        "venue_policy_human_review_completed",
        "final_cfp_policy_frozen_claimed",
        "commercial_runtime_behavior_claimed",
    ):
        require(boundary.get(key) is False, f"claim boundary must remain false: {key}")


def validate_profiles(policy: dict[str, Any]) -> None:
    profiles = load_json(PROFILES_PATH)
    require(
        profiles.get("selected_profile_for_next_external_review") == ANONYMOUS_PROFILE,
        "tracked packaging profile must match selected venue policy",
    )
    selected_profile = policy["selected_policy_target"]["submission_packaging_profile"]
    require(selected_profile == profiles["selected_profile_for_next_external_review"], "selected profile mismatch")
    require(profiles.get("actual_external_submission_claimed") is False, "profile cannot claim external submission")


def validate_docs() -> None:
    policy_doc = POLICY_DOC_PATH.read_text(encoding="utf-8")
    for text in (
        "Status: current official-source snapshot; no external venue submission claimed.",
        "usenix_security_2027_cycle_2",
        "python3 tools/validate_selected_venue_policy.py --venue-metadata-dir tmp/venue-package-metadata",
        "Refresh official venue sources immediately before any real external",
    ):
        require(text in policy_doc, f"selected venue policy doc missing: {text}")

    packaging_pass = PACKAGING_PASS_PATH.read_text(encoding="utf-8")
    require("selected-venue policy snapshot" in packaging_pass, "venue packaging pass must mention selected-venue policy snapshot")
    require("tools/validate_selected_venue_policy.py" in packaging_pass, "venue packaging pass must include selected policy validation")

    ai_disclosure = AI_DISCLOSURE_PATH.read_text(encoding="utf-8")
    require("selected-venue policy snapshot" in ai_disclosure, "AI disclosure must reference selected policy snapshot")
    require("manual finalization" in ai_disclosure, "AI disclosure must remain manual-finalization gated")

    release_checklist = RELEASE_CHECKLIST_PATH.read_text(encoding="utf-8")
    require("python3 tools/validate_selected_venue_policy.py" in release_checklist, "release checklist missing selected policy validator")

    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    require("selected-venue policy snapshot" in roadmap, "roadmap must record selected-venue policy snapshot")
    require("final 2027 CFP/CFA" in roadmap, "roadmap must preserve final CFP/CFA refresh boundary")

    todo = TODO_PATH.read_text(encoding="utf-8")
    require("selected-venue policy snapshot" in todo, "TODO must record selected-venue policy snapshot")
    require("final 2027 CFP/CFA" in todo, "TODO must preserve final CFP/CFA refresh boundary")

    paper_spine = PAPER_SPINE_PATH.read_text(encoding="utf-8")
    require("Official venue sources checked on 2026-06-01" in paper_spine, "paper spine source date must be refreshed")
    require("USENIX Security 2027 Cycle 2 deadline, January 26, 2027" in paper_spine, "paper spine USENIX target missing")


def validate_venue_metadata_bundle(bundle_dir: Path | None, policy: dict[str, Any]) -> None:
    if bundle_dir is None:
        return
    resolved = bundle_dir if bundle_dir.is_absolute() else REPO_ROOT / bundle_dir
    require(resolved.is_dir(), f"venue metadata bundle missing: {resolved}")
    manifest = load_json(resolved / "manifest.json")
    selected_profile = policy["selected_policy_target"]["submission_packaging_profile"]
    require(manifest.get("selected_profile_for_next_external_review") == selected_profile, "metadata bundle selected profile mismatch")
    require(manifest.get("actual_external_submission_claimed") is False, "metadata bundle cannot claim external submission")
    require(manifest.get("profiles") == [ANONYMOUS_PROFILE, PUBLIC_PROFILE], "metadata bundle profile list mismatch")
    require((resolved / ANONYMOUS_PROFILE / "CITATION.cff").is_file(), "anonymous CFF overlay missing")
    require((resolved / PUBLIC_PROFILE / "CITATION.cff").is_file(), "public CFF overlay missing")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--venue-metadata-dir",
        type=Path,
        default=None,
        help="optional venue metadata bundle directory to cross-check",
    )
    args = parser.parse_args(argv)

    policy = load_json(POLICY_PATH)
    require(isinstance(policy, dict), "selected venue policy must parse as a JSON object")
    validate_policy(policy)
    validate_profiles(policy)
    validate_docs()
    validate_venue_metadata_bundle(args.venue_metadata_dir, policy)
    print("validated selected venue policy snapshot")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"selected venue policy validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
