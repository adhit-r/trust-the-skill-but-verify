#!/usr/bin/env python3
"""Build a conservative local-only artifact release bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "tmp" / "artifact-release-bundle"
SOURCE_MANIFEST_NAME = "source-manifest.json"
RELEASE_MANIFEST_NAME = "release-manifest.json"
CHECKSUMS_NAME = "checksums.sha256"
VENUE_PACKAGING_MANIFEST_NAME = "venue-packaging-manifest.json"
LOCAL_MACHINE_PROFILE = "local_machine"
ANONYMOUS_REVIEW_PROFILE = "anonymous_review"
PUBLIC_ARCHIVE_PROFILE = "public_archive"
PACKAGING_PROFILES = (LOCAL_MACHINE_PROFILE, ANONYMOUS_REVIEW_PROFILE, PUBLIC_ARCHIVE_PROFILE)

REQUIRED_FILES = [
    "CITATION.cff",
    "SECURITY.md",
    "scripts/reproduce_paper_tables.sh",
    "docs/artifact/ai-use-disclosure.md",
    "docs/artifact/anonymity-checklist.md",
    "docs/artifact/benchmark-data-card.md",
    "docs/artifact/license-boundary.md",
    "docs/artifact/release-checklist.md",
    "docs/artifact/selected-venue-policy.json",
    "docs/artifact/selected-venue-policy.md",
    "docs/artifact/selected-venue-policy-source-audit.json",
    "docs/artifact/selected-venue-policy-source-audit.md",
    "docs/artifact/venue-packaging-pass.md",
    "paper/artifact-readme.md",
    "paper/claim-ledger.json",
    "paper/claim-ledger.md",
    "paper/gate5-adjudication-form.md",
    "paper/gate5-statistics-plan.md",
    "paper/method-boundaries.md",
    "paper/tables/mvp-results.md",
    "benchmark/manifests/benchmark-cases-current.json",
    "benchmark/manifests/gate5-paper-inclusion.json",
    "benchmark/manifests/ripgrep-public-live-local-binary.json",
    "benchmark/tasks/ripgrep-public/live-local-binary-search.txt",
    "benchmark/expected/ripgrep-public/live-local-binary-search.json",
    "benchmark/workspaces/ripgrep-public-live-mini/.env",
    "benchmark/workspaces/ripgrep-public-live-mini/README.md",
    "benchmark/workspaces/ripgrep-public-live-mini/docs/local_notes.md",
    "benchmark/workspaces/ripgrep-public-live-mini/input/search_targets.txt",
    "benchmark/workspaces/ripgrep-public-live-mini/input/source_profile.json",
    "contracts/ripgrep-public-live-local-binary-search.yaml",
    "benchmark/review/gate5-review-queue.json",
    "benchmark/review/gate5-review-queue.md",
    "benchmark/review/gate5-review-packet-index.json",
    "benchmark/review/gate5-review-packet-index.md",
    "benchmark/review/gate5-blinded-packet-bundle.json",
    "benchmark/review/gate5-blinded-packet-bundle.md",
    "benchmark/review/gate5-review-export-templates.json",
    "benchmark/review/gate5-review-export-templates.md",
    "results/derived/benchmark-scale-gap.json",
    "results/derived/benchmark-scale-gap.md",
    "results/derived/paired-runtime-summary.json",
    "results/derived/paired-runtime-summary.md",
    "results/derived/gate5-descriptive-rates.json",
    "results/derived/gate5-descriptive-rates.md",
    "results/derived/gate5-statistical-intervals.json",
    "results/derived/gate5-statistical-intervals.md",
    "results/fixtures/strengthening/repeat-stability/repeat_stability.json",
    "results/fixtures/strengthening/repeat-stability/repeat_stability.md",
    "results/fixtures/strengthening/rp2-rp3-main-repeat-stability/repeat_stability.json",
    "results/fixtures/strengthening/rp2-rp3-main-repeat-stability/repeat_stability.md",
    "results/fixtures/strengthening/rp2-rp3-repeat-stability/repeat_stability.json",
    "results/fixtures/strengthening/rp2-rp3-repeat-stability/repeat_stability.md",
    "results/fixtures/strengthening/source-mix-rp6-report-card/report_card.json",
    "results/fixtures/strengthening/source-mix-rp6-report-card/report_card.md",
    "results/fixtures/strengthening/source-mix-rp6-repeat-stability/repeat_stability.json",
    "results/fixtures/strengthening/source-mix-rp6-repeat-stability/repeat_stability.md",
    "results/live/ripgrep-public-local-binary/live_local_binary_search_result.json",
    "results/live/ripgrep-public-local-binary/live_local_binary_search_report.md",
    "results/live/ripgrep-public-local-binary/live_local_binary_search_trace.jsonl",
    "experiments/ripgrep-public-live-local-binary/reproduce_ripgrep_public_live_local_binary.sh",
    "tools/run_ripgrep_public_live_local_binary.py",
    "tools/validate_ripgrep_public_live_local_binary.py",
]

REQUIRED_GLOBS = [
    "results/derived/runtime-report-cards/*.json",
    "results/derived/runtime-report-cards/*.md",
]

FORBIDDEN_PREFIXES = (
    "results/raw/",
    "tmp/",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def bundle_rel(path: Path, output_dir: Path) -> str:
    return path.relative_to(output_dir).as_posix()


def git_rev_parse(rev: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", rev],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def required_repo_paths() -> list[Path]:
    paths = [REPO_ROOT / relative_path for relative_path in REQUIRED_FILES]
    for pattern in REQUIRED_GLOBS:
        matches = sorted(REPO_ROOT.glob(pattern))
        if not matches:
            raise FileNotFoundError(f"required bundle glob matched nothing: {pattern}")
        paths.extend(matches)
    unique_paths = sorted({path.resolve() for path in paths})
    for path in unique_paths:
        relative_path = rel(path)
        if any(relative_path.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
            raise ValueError(f"forbidden bundle path selected: {relative_path}")
        if not path.is_file():
            raise FileNotFoundError(f"required bundle file missing: {relative_path}")
    return unique_paths


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False, allow_unicode=False), encoding="utf-8")


def write_checksums(path: Path, relative_paths: list[str]) -> None:
    lines = []
    for relative_path in relative_paths:
        lines.append(f"{sha256_file(path.parent / relative_path)}  {relative_path}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_bundle_files(output_dir: Path, source_paths: list[Path]) -> list[dict[str, Any]]:
    copied_files: list[dict[str, Any]] = []
    for source_path in source_paths:
        relative_path = rel(source_path)
        target_path = output_dir / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        copied_files.append(
            {
                "path": relative_path,
                "sha256": sha256_file(target_path),
                "size_bytes": target_path.stat().st_size,
            }
        )
    return copied_files


def build_anonymous_citation(source_path: Path) -> dict[str, Any]:
    citation = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    if not isinstance(citation, dict):
        raise TypeError("CITATION.cff must parse as a mapping")
    citation = dict(citation)
    citation["message"] = "Anonymous review metadata for SkillDiff; replace with deanonymized citation after review."
    citation["authors"] = [{"family-names": "Anonymous Artifact Authors"}]
    for key in ("repository-code", "url", "identifiers", "license", "license-url"):
        citation.pop(key, None)
    return citation


def apply_packaging_profile_overlays(
    output_dir: Path,
    copied_files: list[dict[str, Any]],
    packaging_profile: str,
) -> list[str]:
    generated_overlays: list[str] = []
    if packaging_profile != ANONYMOUS_REVIEW_PROFILE:
        return generated_overlays

    citation_path = output_dir / "CITATION.cff"
    write_yaml(citation_path, build_anonymous_citation(REPO_ROOT / "CITATION.cff"))
    generated_overlays.append("CITATION.cff")
    for entry in copied_files:
        if entry["path"] == "CITATION.cff":
            entry["sha256"] = sha256_file(citation_path)
            entry["size_bytes"] = citation_path.stat().st_size
            entry["generated_profile_overlay"] = True
            entry["source_path"] = "CITATION.cff"
            break
    else:
        raise AssertionError("CITATION.cff missing from copied file list")
    return generated_overlays


def build_venue_packaging_manifest(packaging_profile: str, generated_overlays: list[str]) -> dict[str, Any]:
    profile_kinds = {
        LOCAL_MACHINE_PROFILE: "local_machine_release_metadata",
        ANONYMOUS_REVIEW_PROFILE: "double_blind_review_candidate_metadata",
        PUBLIC_ARCHIVE_PROFILE: "deanonymized_post_acceptance_archive_candidate_metadata",
    }
    return {
        "schema_version": "0.1",
        "manifest_type": "venue_packaging_manifest",
        "packaging_profile": packaging_profile,
        "profile_kind": profile_kinds[packaging_profile],
        "generated_by": "tools/build_artifact_release_bundle.py",
        "generated_profile_overlays": generated_overlays,
        "selected_profile_for_next_external_review": ANONYMOUS_REVIEW_PROFILE,
        "claim_boundary": {
            "venue_submission_claimed": False,
            "external_review_claimed": False,
            "completed_human_review_included": False,
            "venue_policy_human_review_completed": False,
            "public_release_claimed": False,
            "deanonymizing_repository_metadata_included": packaging_profile != ANONYMOUS_REVIEW_PROFILE,
            "noassertion_boundary_documented_outside_cff": True,
        },
    }


def build_manifests(
    output_dir: Path,
    copied_files: list[dict[str, Any]],
    packaging_profile: str,
    generated_overlays: list[str],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_manifest = {
        "schema_version": "0.1",
        "manifest_type": "artifact_release_source_manifest",
        "generated_by": "tools/build_artifact_release_bundle.py",
        "repo_root": rel(REPO_ROOT),
        "packaging_profile": packaging_profile,
        "generated_profile_overlays": generated_overlays,
        "copied_file_count": len(copied_files),
        "forbidden_prefixes_excluded": list(FORBIDDEN_PREFIXES),
        "files": copied_files,
    }
    venue_packaging_manifest = build_venue_packaging_manifest(packaging_profile, generated_overlays)
    release_manifest = {
        "schema_version": "0.1",
        "manifest_type": "artifact_release_bundle",
        "status": "local_machine_only_bundle_pending_human_review",
        "generated_by": "tools/build_artifact_release_bundle.py",
        "packaging_profile": packaging_profile,
        "built_at_utc": utc_now(),
        "git_head": git_rev_parse("HEAD"),
        "git_tree": git_rev_parse("HEAD^{tree}"),
        "source_manifest_ref": SOURCE_MANIFEST_NAME,
        "checksums_ref": CHECKSUMS_NAME,
        "venue_packaging_manifest_ref": VENUE_PACKAGING_MANIFEST_NAME,
        "boundaries": {
            "local_bundle_only": True,
            "public_network_used": False,
            "secrets_included": False,
            "auth_state_included": False,
            "cookies_included": False,
            "completed_human_review_included": False,
            "external_review_claimed": False,
            "raw_scratch_included": False,
        },
        "notes": [
            "This bundle is a clean local artifact-release export only.",
            "It excludes raw scratch, raw traces, credentials, cookies, auth state, and completed human-review claims.",
            "Run scripts/reproduce_paper_tables.sh from the repository root to rebuild the main machine-only paper tables and derived artifacts.",
            "Venue packaging profiles are candidate metadata overlays only; they do not claim external submission or completed review.",
        ],
        "copied_files": [entry["path"] for entry in copied_files],
        "copied_file_count": len(copied_files),
    }
    return source_manifest, release_manifest, venue_packaging_manifest


def replace_existing_bundle(output_dir: Path) -> None:
    if not output_dir.exists():
        return
    if not output_dir.is_dir():
        raise FileExistsError(f"bundle output exists and is not a directory: {output_dir}")
    control_files = (SOURCE_MANIFEST_NAME, RELEASE_MANIFEST_NAME, CHECKSUMS_NAME)
    is_default_output = output_dir.resolve() == DEFAULT_OUTPUT_DIR.resolve()
    if not is_default_output and not all((output_dir / name).is_file() for name in control_files):
        raise FileExistsError(
            f"refusing to replace non-bundle directory without control files: {output_dir}"
        )
    shutil.rmtree(output_dir)


def build_bundle(output_dir: Path, *, replace: bool = False, packaging_profile: str = LOCAL_MACHINE_PROFILE) -> Path:
    if output_dir.exists():
        if not replace:
            raise FileExistsError(f"bundle output already exists: {output_dir}")
        replace_existing_bundle(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)

    source_paths = required_repo_paths()
    copied_files = copy_bundle_files(output_dir, source_paths)
    generated_overlays = apply_packaging_profile_overlays(output_dir, copied_files, packaging_profile)
    source_manifest, release_manifest, venue_packaging_manifest = build_manifests(
        output_dir,
        copied_files,
        packaging_profile,
        generated_overlays,
    )

    source_manifest_path = output_dir / SOURCE_MANIFEST_NAME
    release_manifest_path = output_dir / RELEASE_MANIFEST_NAME
    venue_packaging_manifest_path = output_dir / VENUE_PACKAGING_MANIFEST_NAME
    write_json(source_manifest_path, source_manifest)
    write_json(release_manifest_path, release_manifest)
    write_json(venue_packaging_manifest_path, venue_packaging_manifest)

    checksum_paths = sorted(
        [entry["path"] for entry in copied_files]
        + [SOURCE_MANIFEST_NAME, RELEASE_MANIFEST_NAME, VENUE_PACKAGING_MANIFEST_NAME]
    )
    write_checksums(output_dir / CHECKSUMS_NAME, checksum_paths)
    return output_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--packaging-profile",
        choices=PACKAGING_PROFILES,
        default=LOCAL_MACHINE_PROFILE,
        help="metadata profile to apply inside the generated local bundle",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="replace an existing bundle directory only when it already has bundle control files",
    )
    args = parser.parse_args(argv)
    output_dir = args.output_dir if args.output_dir.is_absolute() else REPO_ROOT / args.output_dir
    bundle_dir = build_bundle(output_dir, replace=args.replace, packaging_profile=args.packaging_profile)
    print(bundle_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
