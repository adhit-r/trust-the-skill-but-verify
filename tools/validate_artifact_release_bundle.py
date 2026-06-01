#!/usr/bin/env python3
"""Validate the conservative local-only artifact release bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_ROOT))

from build_artifact_release_bundle import REQUIRED_FILES, REQUIRED_GLOBS  # noqa: E402

DEFAULT_BUNDLE_DIR = REPO_ROOT / "tmp" / "artifact-release-bundle"
SOURCE_MANIFEST_NAME = "source-manifest.json"
RELEASE_MANIFEST_NAME = "release-manifest.json"
CHECKSUMS_NAME = "checksums.sha256"
VENUE_PACKAGING_MANIFEST_NAME = "venue-packaging-manifest.json"
LOCAL_MACHINE_PROFILE = "local_machine"
ANONYMOUS_REVIEW_PROFILE = "anonymous_review"
PUBLIC_ARCHIVE_PROFILE = "public_archive"
PACKAGING_PROFILES = (LOCAL_MACHINE_PROFILE, ANONYMOUS_REVIEW_PROFILE, PUBLIC_ARCHIVE_PROFILE)
FORBIDDEN_PREFIXES = ("results/raw/", "tmp/")
EXPECTED_REPOSITORY = "https://github.com/adhit-r/trust-the-skill-but-verify"
BLOCKED_ANONYMOUS_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"adhit-r",
        r"trust-the-skill-but-verify",
        r"github\.com/adhit-r",
    )
]
LOCAL_PATH_PATTERNS = [
    re.compile(pattern)
    for pattern in (
        "/" + r"Users/[^/\s\"']+",
        "/" + "private/" + r"var/folders/[^\s\"']+",
        "/" + "var/" + r"folders/[^\s\"']+",
    )
]
SECRET_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"(api[_-]?key|secret|token|cookie|authorization)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}",
        r"bearer\s+[A-Za-z0-9_\-\.]{20,}",
    )
]


try:
    import yaml
except Exception:  # pragma: no cover - verify installs PyYAML
    yaml = None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> Any:
    require(yaml is not None, "PyYAML is required for CFF validation")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def scan_text_file(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8")
    for line_no, line in enumerate(text.splitlines(), start=1):
        if any(pattern.search(line) for pattern in LOCAL_PATH_PATTERNS):
            findings.append(f"{path.name}:{line_no}: local path")
        if any(pattern.search(line) for pattern in SECRET_PATTERNS):
            findings.append(f"{path.name}:{line_no}: secret-like token")
    return findings


def parse_checksums(path: Path) -> dict[str, str]:
    expected: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, relative_path = line.split("  ", 1)
        expected[relative_path] = digest
    return expected


def expected_required_bundle_paths() -> list[str]:
    paths = [relative_path for relative_path in REQUIRED_FILES]
    for pattern in REQUIRED_GLOBS:
        matches = sorted(REPO_ROOT.glob(pattern))
        if not matches:
            raise FileNotFoundError(f"required bundle glob matched nothing: {pattern}")
        paths.extend(path.relative_to(REPO_ROOT).as_posix() for path in matches)
    return sorted(set(paths))


def validate_venue_packaging_manifest(
    manifest: dict[str, Any],
    packaging_profile: str,
    generated_overlays: list[str],
) -> None:
    require(manifest.get("schema_version") == "0.1", "venue packaging manifest schema mismatch")
    require(
        manifest.get("manifest_type") == "venue_packaging_manifest",
        "venue packaging manifest type mismatch",
    )
    require(manifest.get("packaging_profile") == packaging_profile, "venue packaging profile mismatch")
    require(
        manifest.get("selected_profile_for_next_external_review") == ANONYMOUS_REVIEW_PROFILE,
        "selected external-review profile mismatch",
    )
    require(
        manifest.get("generated_profile_overlays") == generated_overlays,
        "venue packaging overlay list mismatch",
    )
    boundary = manifest.get("claim_boundary", {})
    for key in (
        "venue_submission_claimed",
        "external_review_claimed",
        "completed_human_review_included",
        "venue_policy_human_review_completed",
        "public_release_claimed",
    ):
        require(boundary.get(key) is False, f"venue boundary {key} must be false")
    require(
        boundary.get("deanonymizing_repository_metadata_included")
        is (packaging_profile != ANONYMOUS_REVIEW_PROFILE),
        "deanonymizing metadata boundary mismatch",
    )
    require(
        boundary.get("noassertion_boundary_documented_outside_cff") is True,
        "NOASSERTION boundary must remain documented outside CFF",
    )


def validate_citation_profile(bundle_dir: Path, packaging_profile: str) -> None:
    citation_path = bundle_dir / "CITATION.cff"
    citation = load_yaml(citation_path)
    require(isinstance(citation, dict), "bundled CITATION.cff must parse as a mapping")
    require("license" not in citation, "bundled CITATION.cff must omit license until a real SPDX license is selected")
    require("license-url" not in citation, "bundled CITATION.cff must omit license-url until a license is selected")

    if packaging_profile == ANONYMOUS_REVIEW_PROFILE:
        text = citation_path.read_text(encoding="utf-8")
        require("repository-code" not in citation, "anonymous review CFF must omit repository-code")
        require("url" not in citation, "anonymous review CFF must omit url")
        require("identifiers" not in citation, "anonymous review CFF must omit identifiers")
        require(
            citation.get("authors") == [{"family-names": "Anonymous Artifact Authors"}],
            "anonymous review CFF authors mismatch",
        )
        require(
            not any(pattern.search(text) for pattern in BLOCKED_ANONYMOUS_PATTERNS),
            "anonymous review CFF contains deanonymizing repository metadata",
        )
        return

    require(
        citation.get("repository-code") == EXPECTED_REPOSITORY,
        "deanonymized/local CFF repository-code mismatch",
    )
    require(isinstance(citation.get("authors"), list) and citation["authors"], "deanonymized/local CFF authors missing")


def validate_selected_venue_policy_files(bundle_dir: Path) -> None:
    policy = load_json(bundle_dir / "docs" / "artifact" / "selected-venue-policy.json")
    audit = load_json(bundle_dir / "docs" / "artifact" / "selected-venue-policy-source-audit.json")
    policy_doc = (bundle_dir / "docs" / "artifact" / "selected-venue-policy.md").read_text(encoding="utf-8")
    audit_doc = (bundle_dir / "docs" / "artifact" / "selected-venue-policy-source-audit.md").read_text(encoding="utf-8")

    require(
        policy.get("source_audit_ref") == "docs/artifact/selected-venue-policy-source-audit.json",
        "bundled selected-venue policy source audit ref mismatch",
    )
    require(
        policy["snapshot"]["final_submission_policy_check_complete"] is False,
        "bundled selected-venue policy cannot claim final policy check",
    )
    require(
        policy["snapshot"]["requires_refresh_before_submission"] is True,
        "bundled selected-venue policy must require pre-submission refresh",
    )
    require(
        audit.get("status") == "official_source_audit_ready_final_freeze_open",
        "bundled selected-venue source audit status mismatch",
    )
    require(audit.get("source_count") == 7, "bundled selected-venue source audit source count mismatch")
    require(
        audit["submission_readiness_effect"]["can_close_final_selected_venue_policy_refresh_dependency"] is False,
        "bundled selected-venue source audit cannot close final venue dependency",
    )
    require(
        audit["claim_boundary"]["final_cfp_policy_frozen_claimed"] is False,
        "bundled selected-venue source audit cannot claim final CFP/CFA freeze",
    )
    require("final selected-venue policy refresh" in policy_doc, "bundled selected-venue policy doc boundary missing")
    require(
        "It does not close the final selected-venue policy refresh dependency." in audit_doc,
        "bundled source audit doc boundary missing",
    )


def scan_anonymous_bundle(bundle_dir: Path) -> list[str]:
    findings: list[str] = []
    for path in sorted(bundle_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in {".cff", ".env", ".json", ".jsonl", ".md", ".py", ".sh", ".txt", ".yaml", ".yml"}:
            continue
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if any(pattern.search(line) for pattern in BLOCKED_ANONYMOUS_PATTERNS):
                findings.append(f"{path.relative_to(bundle_dir)}:{line_no}: deanonymizing repository metadata")
    return findings


def validate_bundle(bundle_dir: Path, packaging_profile: str = LOCAL_MACHINE_PROFILE) -> None:
    require(bundle_dir.is_dir(), f"bundle directory missing: {bundle_dir}")
    source_manifest_path = bundle_dir / SOURCE_MANIFEST_NAME
    release_manifest_path = bundle_dir / RELEASE_MANIFEST_NAME
    checksums_path = bundle_dir / CHECKSUMS_NAME
    venue_packaging_manifest_path = bundle_dir / VENUE_PACKAGING_MANIFEST_NAME
    for required_path in (source_manifest_path, release_manifest_path, checksums_path, venue_packaging_manifest_path):
        require(required_path.is_file(), f"missing bundle control file: {required_path.name}")

    source_manifest = load_json(source_manifest_path)
    release_manifest = load_json(release_manifest_path)
    venue_packaging_manifest = load_json(venue_packaging_manifest_path)
    expected_checksums = parse_checksums(checksums_path)

    require(source_manifest.get("schema_version") == "0.1", "source manifest schema mismatch")
    require(
        source_manifest.get("manifest_type") == "artifact_release_source_manifest",
        "source manifest type mismatch",
    )
    require(release_manifest.get("schema_version") == "0.1", "release manifest schema mismatch")
    require(
        release_manifest.get("manifest_type") == "artifact_release_bundle",
        "release manifest type mismatch",
    )
    require(
        release_manifest.get("status") == "local_machine_only_bundle_pending_human_review",
        "release manifest status mismatch",
    )
    require(source_manifest.get("packaging_profile") == packaging_profile, "source manifest packaging profile mismatch")
    require(release_manifest.get("packaging_profile") == packaging_profile, "release manifest packaging profile mismatch")
    require(release_manifest.get("source_manifest_ref") == SOURCE_MANIFEST_NAME, "source manifest ref mismatch")
    require(release_manifest.get("checksums_ref") == CHECKSUMS_NAME, "checksums ref mismatch")
    require(
        release_manifest.get("venue_packaging_manifest_ref") == VENUE_PACKAGING_MANIFEST_NAME,
        "venue packaging manifest ref mismatch",
    )

    boundaries = release_manifest.get("boundaries", {})
    require(boundaries.get("local_bundle_only") is True, "bundle must remain local only")
    for key in (
        "public_network_used",
        "secrets_included",
        "auth_state_included",
        "cookies_included",
        "completed_human_review_included",
        "external_review_claimed",
        "raw_scratch_included",
    ):
        require(boundaries.get(key) is False, f"boundary {key} must be false")

    copied_files = source_manifest.get("files", [])
    generated_overlays = source_manifest.get("generated_profile_overlays", [])
    require(isinstance(generated_overlays, list), "generated overlay list must be a list")
    expected_overlays = ["CITATION.cff"] if packaging_profile == ANONYMOUS_REVIEW_PROFILE else []
    require(generated_overlays == expected_overlays, "generated overlay list mismatch")
    validate_venue_packaging_manifest(venue_packaging_manifest, packaging_profile, generated_overlays)
    validate_citation_profile(bundle_dir, packaging_profile)
    validate_selected_venue_policy_files(bundle_dir)
    require(isinstance(copied_files, list) and copied_files, "bundle file list must be non-empty")
    require(
        release_manifest.get("copied_file_count") == len(copied_files),
        "release manifest copied-file count mismatch",
    )

    copied_paths = [entry["path"] for entry in copied_files]
    required_paths = expected_required_bundle_paths()
    missing_required_paths = sorted(set(required_paths) - set(copied_paths))
    require(
        not missing_required_paths,
        f"bundle missing required current file set: {missing_required_paths[:5]}",
    )
    require(
        release_manifest.get("copied_files") == copied_paths,
        "release manifest copied file list mismatch",
    )
    require(
        source_manifest.get("copied_file_count") == len(copied_files),
        "source manifest copied-file count mismatch",
    )
    require(
        source_manifest.get("forbidden_prefixes_excluded") == list(FORBIDDEN_PREFIXES),
        "source manifest forbidden-prefix boundary mismatch",
    )

    observed_paths = sorted(copied_paths + [SOURCE_MANIFEST_NAME, RELEASE_MANIFEST_NAME, VENUE_PACKAGING_MANIFEST_NAME])
    require(
        sorted(expected_checksums) == observed_paths,
        "checksums must cover copied files and both manifest files",
    )

    hygiene_findings: list[str] = []
    for entry in copied_files:
        relative_path = entry["path"]
        require(not any(relative_path.startswith(prefix) for prefix in FORBIDDEN_PREFIXES), f"forbidden path in bundle: {relative_path}")
        source_path = REPO_ROOT / relative_path
        file_path = bundle_dir / relative_path
        require(file_path.is_file(), f"missing bundled file: {relative_path}")
        observed_digest = sha256_file(file_path)
        if relative_path in generated_overlays:
            require(
                entry.get("generated_profile_overlay") is True,
                f"generated overlay flag missing for {relative_path}",
            )
            require(entry.get("source_path") == relative_path, f"generated overlay source path mismatch for {relative_path}")
        else:
            require(source_path.is_file(), f"missing current repo source file: {relative_path}")
            source_digest = sha256_file(source_path)
            require(observed_digest == source_digest, f"bundled file is stale relative to repo source: {relative_path}")
        require(entry["sha256"] == observed_digest, f"source manifest hash mismatch for {relative_path}")
        require(expected_checksums[relative_path] == observed_digest, f"checksum mismatch for {relative_path}")
        if file_path.suffix in {".env", ".json", ".jsonl", ".md", ".py", ".sh", ".txt", ".yaml", ".yml"}:
            hygiene_findings.extend(scan_text_file(file_path))

    for control_path in (source_manifest_path, release_manifest_path, venue_packaging_manifest_path):
        observed_digest = sha256_file(control_path)
        require(expected_checksums[control_path.name] == observed_digest, f"checksum mismatch for {control_path.name}")
        hygiene_findings.extend(scan_text_file(control_path))

    require(not hygiene_findings, f"bundle hygiene scan failed: {hygiene_findings[:3]}")
    if packaging_profile == ANONYMOUS_REVIEW_PROFILE:
        anonymous_findings = scan_anonymous_bundle(bundle_dir)
        require(not anonymous_findings, f"anonymous bundle deanonymization scan failed: {anonymous_findings[:3]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-dir", type=Path, default=DEFAULT_BUNDLE_DIR)
    parser.add_argument(
        "--packaging-profile",
        choices=PACKAGING_PROFILES,
        default=LOCAL_MACHINE_PROFILE,
        help="expected metadata profile inside the generated local bundle",
    )
    args = parser.parse_args(argv)
    bundle_dir = args.bundle_dir if args.bundle_dir.is_absolute() else REPO_ROOT / args.bundle_dir
    validate_bundle(bundle_dir, packaging_profile=args.packaging_profile)
    print(f"validated artifact release bundle: {bundle_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"artifact release bundle validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
