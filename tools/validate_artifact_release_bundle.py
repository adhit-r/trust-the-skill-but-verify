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
FORBIDDEN_PREFIXES = ("results/raw/", "tmp/")
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def validate_bundle(bundle_dir: Path) -> None:
    require(bundle_dir.is_dir(), f"bundle directory missing: {bundle_dir}")
    source_manifest_path = bundle_dir / SOURCE_MANIFEST_NAME
    release_manifest_path = bundle_dir / RELEASE_MANIFEST_NAME
    checksums_path = bundle_dir / CHECKSUMS_NAME
    for required_path in (source_manifest_path, release_manifest_path, checksums_path):
        require(required_path.is_file(), f"missing bundle control file: {required_path.name}")

    source_manifest = load_json(source_manifest_path)
    release_manifest = load_json(release_manifest_path)
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
    require(release_manifest.get("source_manifest_ref") == SOURCE_MANIFEST_NAME, "source manifest ref mismatch")
    require(release_manifest.get("checksums_ref") == CHECKSUMS_NAME, "checksums ref mismatch")

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

    observed_paths = sorted(copied_paths + [SOURCE_MANIFEST_NAME, RELEASE_MANIFEST_NAME])
    require(
        sorted(expected_checksums) == observed_paths,
        "checksums must cover copied files and both manifest files",
    )

    hygiene_findings: list[str] = []
    for entry in copied_files:
        relative_path = entry["path"]
        require(not any(relative_path.startswith(prefix) for prefix in FORBIDDEN_PREFIXES), f"forbidden path in bundle: {relative_path}")
        source_path = REPO_ROOT / relative_path
        require(source_path.is_file(), f"missing current repo source file: {relative_path}")
        source_digest = sha256_file(source_path)
        file_path = bundle_dir / relative_path
        require(file_path.is_file(), f"missing bundled file: {relative_path}")
        observed_digest = sha256_file(file_path)
        require(observed_digest == source_digest, f"bundled file is stale relative to repo source: {relative_path}")
        require(entry["sha256"] == observed_digest, f"source manifest hash mismatch for {relative_path}")
        require(expected_checksums[relative_path] == observed_digest, f"checksum mismatch for {relative_path}")
        if file_path.suffix in {".env", ".json", ".jsonl", ".md", ".py", ".sh", ".txt", ".yaml", ".yml"}:
            hygiene_findings.extend(scan_text_file(file_path))

    for control_path in (source_manifest_path, release_manifest_path):
        observed_digest = sha256_file(control_path)
        require(expected_checksums[control_path.name] == observed_digest, f"checksum mismatch for {control_path.name}")
        hygiene_findings.extend(scan_text_file(control_path))

    require(not hygiene_findings, f"bundle hygiene scan failed: {hygiene_findings[:3]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-dir", type=Path, default=DEFAULT_BUNDLE_DIR)
    args = parser.parse_args(argv)
    bundle_dir = args.bundle_dir if args.bundle_dir.is_absolute() else REPO_ROOT / args.bundle_dir
    validate_bundle(bundle_dir)
    print(f"validated artifact release bundle: {bundle_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"artifact release bundle validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
