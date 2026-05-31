#!/usr/bin/env python3
"""Validate profile-specific citation metadata for venue packaging."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE_DIR = REPO_ROOT / "tmp" / "venue-package-metadata"
PROFILES_PATH = REPO_ROOT / "docs" / "artifact" / "venue-packaging-profiles.json"
PACKAGING_PASS_PATH = REPO_ROOT / "docs" / "artifact" / "venue-packaging-pass.md"
RELEASE_CHECKLIST_PATH = REPO_ROOT / "docs" / "artifact" / "release-checklist.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "research" / "research-roadmap.md"
TODO_PATH = REPO_ROOT / "docs" / "research" / "research-todo.md"
CITATION_PATH = REPO_ROOT / "CITATION.cff"
EXPECTED_REPOSITORY = "https://github.com/adhit-r/trust-the-skill-but-verify"
ANONYMOUS_PROFILE = "anonymous_review"
PUBLIC_PROFILE = "public_archive"
BLOCKED_ANONYMOUS_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"adhit-r",
        r"trust-the-skill-but-verify",
        r"github\.com/adhit-r",
    )
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_tracked_profiles() -> dict[str, Any]:
    profiles = load_json(PROFILES_PATH)
    require(profiles.get("schema_version") == "0.1", "profile schema mismatch")
    require(
        profiles.get("status") == "packaging_profiles_ready_no_external_submission",
        "profile status mismatch",
    )
    require(
        profiles.get("selected_profile_for_next_external_review") == ANONYMOUS_PROFILE,
        "anonymous review must be selected for the next external-review package",
    )
    require(profiles.get("actual_external_submission_claimed") is False, "external submission cannot be claimed")

    profile_list = profiles.get("profiles")
    require(isinstance(profile_list, list), "profiles must be a list")
    profiles_by_id = {profile.get("profile_id"): profile for profile in profile_list}
    require(set(profiles_by_id) == {ANONYMOUS_PROFILE, PUBLIC_PROFILE}, "expected anonymous and public profiles")

    anonymous = profiles_by_id[ANONYMOUS_PROFILE]
    public = profiles_by_id[PUBLIC_PROFILE]
    require(anonymous["citation_policy"]["repository_code"] == "omit", "anonymous repo policy mismatch")
    require(
        anonymous["citation_policy"]["author_identity"] == "anonymous_artifact_authors",
        "anonymous author policy mismatch",
    )
    require(
        anonymous["citation_policy"]["license"] == "omit_until_real_spdx_license_selected",
        "anonymous license policy mismatch",
    )
    require(
        anonymous["claim_boundary"]["deanonymizing_repository_metadata_included"] is False,
        "anonymous profile must exclude deanonymizing metadata",
    )
    require(
        anonymous["claim_boundary"]["noassertion_boundary_documented_outside_cff"] is True,
        "anonymous NOASSERTION boundary mismatch",
    )
    require(
        public["citation_policy"]["repository_code"] == EXPECTED_REPOSITORY,
        "public archive repo policy mismatch",
    )
    require(
        public["claim_boundary"]["deanonymizing_repository_metadata_included"] is True,
        "public archive deanonymized boundary mismatch",
    )
    for profile in profiles_by_id.values():
        boundary = profile["claim_boundary"]
        require(boundary["external_submission_claimed"] is False, "external submission claim boundary mismatch")
        require(boundary["completed_human_review_claimed"] is False, "human review boundary mismatch")
        require(boundary["public_release_claimed"] is False, "public release boundary mismatch")
    return profiles_by_id


def validate_tracked_docs() -> None:
    packaging_pass = PACKAGING_PASS_PATH.read_text(encoding="utf-8")
    for required_text in (
        "Status: selected packaging-profile pass; no external venue submission claimed.",
        "anonymous_review",
        "public_archive",
        "python3 tools/build_venue_package_metadata.py --replace --output-dir tmp/venue-package-metadata",
        "python3 tools/validate_venue_package_metadata.py --bundle-dir tmp/venue-package-metadata",
        "Do not encode `NOASSERTION` as a CFF license value.",
    ):
        require(required_text in packaging_pass, f"venue packaging pass doc missing: {required_text}")

    release_checklist = RELEASE_CHECKLIST_PATH.read_text(encoding="utf-8")
    require(
        "python3 tools/validate_venue_package_metadata.py" in release_checklist,
        "release checklist must include venue metadata validation",
    )
    require("anonymous_review" in release_checklist, "release checklist must mention anonymous review profile")

    roadmap = ROADMAP_PATH.read_text(encoding="utf-8")
    require("selected packaging-profile pass" in roadmap, "roadmap must record selected packaging-profile pass")

    todo = TODO_PATH.read_text(encoding="utf-8")
    require("selected packaging-profile pass" in todo, "todo must record selected packaging-profile pass")


def validate_source_citation() -> None:
    citation = load_yaml(CITATION_PATH)
    require(isinstance(citation, dict), "CITATION.cff must parse as a mapping")
    require(citation.get("repository-code") == EXPECTED_REPOSITORY, "source CFF repo URL mismatch")
    require("license" not in citation, "source CFF must omit license until a real SPDX license is selected")
    require("license-url" not in citation, "source CFF must omit license-url until a license is selected")


def validate_boundary_file(path: Path, expected_profile: dict[str, Any]) -> None:
    boundary = load_json(path)
    require(boundary.get("schema_version") == "0.1", f"{path}: boundary schema mismatch")
    require(boundary.get("profile_id") == expected_profile["profile_id"], f"{path}: profile id mismatch")
    require(boundary.get("profile_kind") == expected_profile["profile_kind"], f"{path}: profile kind mismatch")
    require(boundary.get("citation_policy") == expected_profile["citation_policy"], f"{path}: policy mismatch")
    require(boundary.get("claim_boundary") == expected_profile["claim_boundary"], f"{path}: claim boundary mismatch")


def validate_anonymous_citation(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    citation = load_yaml(path)
    require(isinstance(citation, dict), "anonymous CFF must parse as a mapping")
    require(citation.get("cff-version") == "1.2.0", "anonymous CFF version mismatch")
    require("repository-code" not in citation, "anonymous CFF must omit repository-code")
    require("url" not in citation, "anonymous CFF must omit url")
    require("identifiers" not in citation, "anonymous CFF must omit identifiers")
    require("license" not in citation, "anonymous CFF must omit license")
    require("license-url" not in citation, "anonymous CFF must omit license-url")
    require(
        citation.get("authors") == [{"family-names": "Anonymous Artifact Authors"}],
        "anonymous CFF authors mismatch",
    )
    require(
        not any(pattern.search(text) for pattern in BLOCKED_ANONYMOUS_PATTERNS),
        "anonymous CFF contains deanonymizing repository metadata",
    )


def validate_public_citation(path: Path) -> None:
    citation = load_yaml(path)
    require(isinstance(citation, dict), "public CFF must parse as a mapping")
    require(citation.get("repository-code") == EXPECTED_REPOSITORY, "public CFF repo URL mismatch")
    require("license" not in citation, "public CFF must omit license until a real SPDX license is selected")
    require("license-url" not in citation, "public CFF must omit license-url until a license is selected")
    require(isinstance(citation.get("authors"), list) and citation["authors"], "public CFF authors missing")


def validate_bundle(bundle_dir: Path, profiles_by_id: dict[str, Any]) -> None:
    require(bundle_dir.is_dir(), f"venue metadata bundle missing: {bundle_dir}")
    manifest = load_json(bundle_dir / "manifest.json")
    require(manifest.get("schema_version") == "0.1", "venue metadata manifest schema mismatch")
    require(manifest.get("manifest_type") == "venue_package_metadata", "venue metadata manifest type mismatch")
    require(manifest.get("status") == "packaging_profiles_ready_no_external_submission", "manifest status mismatch")
    require(manifest.get("selected_profile_for_next_external_review") == ANONYMOUS_PROFILE, "manifest selected profile mismatch")
    require(manifest.get("actual_external_submission_claimed") is False, "manifest external submission claim mismatch")
    require(manifest.get("profiles") == [ANONYMOUS_PROFILE, PUBLIC_PROFILE], "manifest profile order mismatch")

    validate_anonymous_citation(bundle_dir / ANONYMOUS_PROFILE / "CITATION.cff")
    validate_boundary_file(bundle_dir / ANONYMOUS_PROFILE / "boundary.json", profiles_by_id[ANONYMOUS_PROFILE])
    validate_public_citation(bundle_dir / PUBLIC_PROFILE / "CITATION.cff")
    validate_boundary_file(bundle_dir / PUBLIC_PROFILE / "boundary.json", profiles_by_id[PUBLIC_PROFILE])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-dir", type=Path, default=DEFAULT_BUNDLE_DIR)
    args = parser.parse_args(argv)
    bundle_dir = args.bundle_dir if args.bundle_dir.is_absolute() else REPO_ROOT / args.bundle_dir

    profiles_by_id = validate_tracked_profiles()
    validate_tracked_docs()
    validate_source_citation()
    validate_bundle(bundle_dir, profiles_by_id)
    print(f"validated venue package metadata profiles: {bundle_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"venue package metadata validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
