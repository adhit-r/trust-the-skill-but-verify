#!/usr/bin/env python3
"""Build profile-specific citation metadata for venue packaging."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "tmp" / "venue-package-metadata"
PROFILES_PATH = REPO_ROOT / "docs" / "artifact" / "venue-packaging-profiles.json"
CITATION_PATH = REPO_ROOT / "CITATION.cff"
ANONYMOUS_PROFILE = "anonymous_review"
PUBLIC_PROFILE = "public_archive"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_citation() -> dict[str, Any]:
    citation = yaml.safe_load(CITATION_PATH.read_text(encoding="utf-8"))
    if not isinstance(citation, dict):
        raise TypeError("CITATION.cff must parse as a mapping")
    return citation


def write_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False, allow_unicode=False), encoding="utf-8")


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_anonymous_citation(source: dict[str, Any]) -> dict[str, Any]:
    citation = dict(source)
    citation["message"] = "Anonymous review metadata for SkillDiff; replace with deanonymized citation after review."
    citation["authors"] = [{"family-names": "Anonymous Artifact Authors"}]
    for key in ("repository-code", "url", "identifiers", "license", "license-url"):
        citation.pop(key, None)
    return citation


def build_public_citation(source: dict[str, Any]) -> dict[str, Any]:
    citation = dict(source)
    for key in ("license", "license-url"):
        citation.pop(key, None)
    return citation


def profile_boundary(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "profile_id": profile["profile_id"],
        "profile_kind": profile["profile_kind"],
        "audience": profile["audience"],
        "citation_policy": profile["citation_policy"],
        "claim_boundary": profile["claim_boundary"],
        "generated_by": "tools/build_venue_package_metadata.py",
    }


def replace_existing_output(output_dir: Path) -> None:
    if not output_dir.exists():
        return
    if not output_dir.is_dir():
        raise FileExistsError(f"venue metadata output exists and is not a directory: {output_dir}")
    control_files = (
        output_dir / ANONYMOUS_PROFILE / "boundary.json",
        output_dir / PUBLIC_PROFILE / "boundary.json",
    )
    is_default_output = output_dir.resolve() == DEFAULT_OUTPUT_DIR.resolve()
    if not is_default_output and not all(path.is_file() for path in control_files):
        raise FileExistsError(
            f"refusing to replace non-venue-metadata directory without control files: {output_dir}"
        )
    shutil.rmtree(output_dir)


def build_metadata(output_dir: Path, *, replace: bool = False) -> Path:
    if output_dir.exists():
        if not replace:
            raise FileExistsError(f"venue metadata output already exists: {output_dir}")
        replace_existing_output(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)

    profiles = load_json(PROFILES_PATH)
    profiles_by_id = {profile["profile_id"]: profile for profile in profiles["profiles"]}
    source_citation = load_citation()

    write_yaml(output_dir / ANONYMOUS_PROFILE / "CITATION.cff", build_anonymous_citation(source_citation))
    write_json(output_dir / ANONYMOUS_PROFILE / "boundary.json", profile_boundary(profiles_by_id[ANONYMOUS_PROFILE]))

    write_yaml(output_dir / PUBLIC_PROFILE / "CITATION.cff", build_public_citation(source_citation))
    write_json(output_dir / PUBLIC_PROFILE / "boundary.json", profile_boundary(profiles_by_id[PUBLIC_PROFILE]))

    write_json(
        output_dir / "manifest.json",
        {
            "schema_version": "0.1",
            "manifest_type": "venue_package_metadata",
            "status": profiles["status"],
            "selected_profile_for_next_external_review": profiles["selected_profile_for_next_external_review"],
            "actual_external_submission_claimed": profiles["actual_external_submission_claimed"],
            "profiles": [ANONYMOUS_PROFILE, PUBLIC_PROFILE],
            "generated_by": "tools/build_venue_package_metadata.py",
        },
    )
    return output_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="replace an existing output directory only when it already has venue metadata control files",
    )
    args = parser.parse_args(argv)
    output_dir = args.output_dir if args.output_dir.is_absolute() else REPO_ROOT / args.output_dir
    print(build_metadata(output_dir, replace=args.replace))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
