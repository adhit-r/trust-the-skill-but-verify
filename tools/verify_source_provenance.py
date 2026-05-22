#!/usr/bin/env python3
"""Verify first-party fixture and optional source checkout provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SKIP_DIRS = {".git", "__pycache__"}
SKIP_FILES = {".DS_Store"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def workspace_snapshot_hash(root: Path) -> str:
    if not root.is_dir():
        raise FileNotFoundError(f"workspace root does not exist: {root}")

    entries: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in rel_parts) or path.name in SKIP_FILES:
            continue
        rel = path.relative_to(root).as_posix()
        entries.append(f"{rel}\0{sha256_file(path)}\n")

    digest = hashlib.sha256()
    for entry in entries:
        digest.update(entry.encode("utf-8"))
    return digest.hexdigest()


def git_output(source_root: Path, args: list[str]) -> str:
    completed = subprocess.run(
        ["git", "-C", str(source_root), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed in {source_root}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return completed.stdout.strip()


def find_expected_commit(manifest: dict[str, Any]) -> str | None:
    source_boundary = manifest.get("source_boundary", {})
    source_repo = manifest.get("source_repo", {})
    source = manifest.get("source", {})
    return (
        source_boundary.get("fixture_source_commit")
        or source_repo.get("fixture_source_commit")
        or source.get("pinned_commit")
    )


def find_expected_tree(manifest: dict[str, Any]) -> str | None:
    source_boundary = manifest.get("source_boundary", {})
    source = manifest.get("source", {})
    return source_boundary.get("fixture_source_tree") or source.get("pinned_tree")


def verify_workspace(root: Path, manifest_path: Path, manifest: dict[str, Any]) -> None:
    workspace = manifest.get("workspace", {})
    workspace_ref = workspace.get("workspace_ref")
    expected = workspace.get("workspace_snapshot_sha256")
    if not workspace_ref or not expected:
        raise RuntimeError(f"{manifest_path}: workspace.workspace_ref and workspace.workspace_snapshot_sha256 are required")

    actual = workspace_snapshot_hash(root / workspace_ref)
    if actual != expected:
        raise RuntimeError(
            f"{manifest_path}: workspace snapshot mismatch for {workspace_ref}: expected {expected}, observed {actual}"
        )


def verify_source_checkout(manifest_path: Path, manifest: dict[str, Any], source_root: Path) -> None:
    if not source_root.exists():
        raise FileNotFoundError(f"source root does not exist: {source_root}")

    expected_commit = find_expected_commit(manifest)
    if expected_commit:
        actual_commit = git_output(source_root, ["rev-parse", "HEAD"])
        if actual_commit != expected_commit:
            raise RuntimeError(
                f"{manifest_path}: source HEAD mismatch for {source_root}: expected {expected_commit}, observed {actual_commit}"
            )

    expected_tree = find_expected_tree(manifest)
    if expected_tree:
        actual_tree = git_output(source_root, ["rev-parse", "HEAD^{tree}"])
        if actual_tree != expected_tree:
            raise RuntimeError(
                f"{manifest_path}: source tree mismatch for {source_root}: expected {expected_tree}, observed {actual_tree}"
            )

    pinned_hashes = manifest.get("pinned_source_hashes", {})
    for rel_path, expected_hash in sorted(pinned_hashes.items()):
        source_file = source_root / rel_path
        if not source_file.is_file():
            raise FileNotFoundError(f"{manifest_path}: pinned source file missing: {source_file}")
        actual_hash = git_output(source_root, ["hash-object", rel_path])
        if actual_hash != expected_hash:
            raise RuntimeError(
                f"{manifest_path}: pinned source hash mismatch for {rel_path}: expected {expected_hash}, observed {actual_hash}"
            )

    status = git_output(source_root, ["status", "--short"])
    expected_clean = (
        manifest.get("source", {}).get("local_source_tracked_state") == "clean"
        or manifest.get("source_boundary", {}).get("local_source_status") == "clean_tracked_tree"
    )
    if expected_clean and status:
        raise RuntimeError(f"{manifest_path}: source checkout is not clean:\n{status}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--print-workspace-snapshot", action="store_true")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if args.print_workspace_snapshot:
        workspace_ref = manifest.get("workspace", {}).get("workspace_ref")
        if not workspace_ref:
            raise RuntimeError(f"{manifest_path}: workspace.workspace_ref is required")
        print(workspace_snapshot_hash(root / workspace_ref))
        return 0

    verify_workspace(root, manifest_path, manifest)
    if args.source_root:
        verify_source_checkout(manifest_path, manifest, args.source_root.resolve())

    label = manifest.get("manifest_id") or manifest.get("pilot_id") or manifest_path.name
    print(f"provenance verified: {label}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"provenance verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
