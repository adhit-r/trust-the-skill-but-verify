#!/usr/bin/env python3
"""Validate release-facing artifact metadata and license boundaries."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
CITATION_PATH = REPO_ROOT / "CITATION.cff"
LICENSE_BOUNDARY_PATH = REPO_ROOT / "docs" / "artifact" / "license-boundary.md"
RELEASE_CHECKLIST_PATH = REPO_ROOT / "docs" / "artifact" / "release-checklist.md"
ARTIFACT_README_PATH = REPO_ROOT / "paper" / "artifact-readme.md"
EXPECTED_REPOSITORY = "https://github.com/adhit-r/trust-the-skill-but-verify"
TOP_LEVEL_LICENSE_FILENAMES = {
    "COPYING",
    "COPYING.md",
    "COPYING.txt",
    "LICENCE",
    "LICENCE.md",
    "LICENCE.txt",
    "LICENSE",
    "LICENSE.md",
    "LICENSE.txt",
    "UNLICENSE",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_citation() -> dict[str, Any]:
    with CITATION_PATH.open("r", encoding="utf-8") as handle:
        citation = yaml.safe_load(handle)
    require(isinstance(citation, dict), "CITATION.cff must parse as a mapping")
    return citation


def validate_citation(citation: dict[str, Any]) -> None:
    require(citation.get("cff-version") == "1.2.0", "CITATION.cff version mismatch")
    require(
        citation.get("title")
        == "SkillDiff: Differential Runtime Conformance Testing for Portable AI Agent Skills",
        "CITATION.cff title mismatch",
    )
    require(citation.get("type") == "software", "CITATION.cff type must be software")
    require(
        citation.get("repository-code") == EXPECTED_REPOSITORY,
        "CITATION.cff repository-code mismatch",
    )
    require("license" not in citation, "CITATION.cff must omit license until a real SPDX license is selected")
    require("license-url" not in citation, "CITATION.cff must omit license-url until a license is selected")
    require(citation.get("date-released") == "2026-05-31", "CITATION.cff release date mismatch")
    require(
        "example.invalid" not in CITATION_PATH.read_text(encoding="utf-8"),
        "CITATION.cff contains placeholder URL",
    )

    authors = citation.get("authors")
    require(isinstance(authors, list) and authors, "CITATION.cff authors must be non-empty")


def validate_boundary_docs() -> None:
    present_license_files = sorted(
        path.name
        for path in REPO_ROOT.iterdir()
        if path.is_file() and path.name in TOP_LEVEL_LICENSE_FILENAMES
    )
    require(
        not present_license_files,
        "CITATION.cff omits license, but top-level license file(s) exist: "
        + ", ".join(present_license_files),
    )

    boundary = LICENSE_BOUNDARY_PATH.read_text(encoding="utf-8")
    require("NOASSERTION" in boundary, "license boundary must explain NOASSERTION")
    require(
        "no top-level open-source license file" in boundary,
        "license boundary must state missing LICENSE",
    )
    require(
        "not a missing placeholder" in boundary,
        "license boundary must mark the boundary intentional",
    )

    artifact_readme = ARTIFACT_README_PATH.read_text(encoding="utf-8")
    require(
        "- [x] Finalize citation metadata and explicit license boundary." in artifact_readme,
        "artifact README checklist must close citation/license metadata",
    )

    release_checklist = RELEASE_CHECKLIST_PATH.read_text(encoding="utf-8")
    require(
        "python3 tools/validate_artifact_metadata.py" in release_checklist,
        "release checklist must include artifact metadata validation",
    )


def main() -> int:
    validate_citation(load_citation())
    validate_boundary_docs()
    print("validated artifact metadata and license boundary")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"artifact metadata validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
