#!/usr/bin/env python3
"""Verify first-party source provenance from clean ephemeral clones."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

SOURCES = [
    {
        "case_id": "docs-forge",
        "manifest": "benchmark/manifests/docs-forge-mini.json",
        "remote_url": "https://github.com/adhit-r/docs-forge.git",
        "workload_boundary": "controlled Python docs-forge-style fixture",
        "product_execution_claim": "real docs-forge Node installer not executed",
    },
    {
        "case_id": "audit-lens",
        "manifest": "benchmark/manifests/audit-lens-acme.json",
        "remote_url": "https://github.com/adhit-r/audit-lens.git",
        "workload_boundary": "sanitized synthetic AuditLens Acme fixture",
        "product_execution_claim": "full AuditLens product and live connectors not executed",
    },
]


def run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)


def run_required(args: list[str], cwd: Path | None = None) -> str:
    completed = run(args, cwd=cwd)
    if completed.returncode != 0:
        command = " ".join(args)
        raise RuntimeError(
            f"command failed ({completed.returncode}): {command}\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return completed.stdout.strip()


def object_value(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def expected_commit(manifest: dict[str, Any]) -> str:
    source_boundary = object_value(manifest.get("source_boundary"))
    source_repo = object_value(manifest.get("source_repo"))
    source = object_value(manifest.get("source"))
    value = (
        source_boundary.get("fixture_source_commit")
        or source_repo.get("fixture_source_commit")
        or source.get("pinned_commit")
    )
    if not isinstance(value, str) or not value:
        raise RuntimeError("manifest is missing a pinned source commit")
    return value


def expected_tree(manifest: dict[str, Any]) -> str:
    source_boundary = object_value(manifest.get("source_boundary"))
    source_repo = object_value(manifest.get("source_repo"))
    source = object_value(manifest.get("source"))
    value = (
        source_boundary.get("fixture_source_tree")
        or source_repo.get("fixture_source_tree")
        or source.get("pinned_tree")
    )
    if not isinstance(value, str) or not value:
        raise RuntimeError("manifest is missing a pinned source tree")
    return value


def sanitize_error(message: str, source_root: Path) -> str:
    return (
        message.replace(str(source_root), "<EPHEMERAL_SOURCE_ROOT>")
        .replace(str(REPO_ROOT), "<REPO_ROOT>")
    )


def clone_and_verify(source: dict[str, str], base_dir: Path) -> dict[str, Any]:
    manifest_ref = source["manifest"]
    manifest_path = REPO_ROOT / manifest_ref
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    commit = expected_commit(manifest)
    tree = expected_tree(manifest)
    clone_root = base_dir / source["case_id"]

    record: dict[str, Any] = {
        "case_id": source["case_id"],
        "source_repo": manifest.get("source_boundary", {}).get("source_repo")
        or manifest.get("source_repo", {}).get("name")
        or source["case_id"],
        "remote_url": source["remote_url"],
        "manifest_ref": manifest_ref,
        "expected_commit": commit,
        "expected_tree": tree,
        "workload_boundary": source["workload_boundary"],
        "product_execution_claim": source["product_execution_claim"],
        "evidence_scope": "ephemeral_clean_clone_source_provenance_only",
        "full_source_vendored": False,
        "full_product_workload_executed": False,
        "real_secrets_present": False,
        "public_internet_contacted_by_benchmark": False,
        "pinned_source_hash_count": len(manifest.get("pinned_source_hashes", {})),
    }

    try:
        run_required(["git", "clone", "--quiet", source["remote_url"], str(clone_root)])
        run_required(["git", "checkout", "--quiet", commit], cwd=clone_root)
        observed_commit = run_required(["git", "rev-parse", "HEAD"], cwd=clone_root)
        observed_tree = run_required(["git", "rev-parse", "HEAD^{tree}"], cwd=clone_root)
        status = run_required(["git", "status", "--short"], cwd=clone_root)

        verify_command = [
            PYTHON,
            "tools/verify_source_provenance.py",
            "--manifest",
            manifest_ref,
            "--source-root",
            str(clone_root),
        ]
        verify = run(verify_command, cwd=REPO_ROOT)
        if verify.returncode != 0:
            raise RuntimeError(
                "source provenance verifier failed\n"
                f"STDOUT:\n{verify.stdout}\nSTDERR:\n{verify.stderr}"
            )

        record.update(
            {
                "verification_status": "passed",
                "observed_commit": observed_commit,
                "observed_tree": observed_tree,
                "clean_worktree": status == "",
                "workspace_fixture_verified": True,
                "pinned_source_hashes_verified": True,
                "verification_command": (
                    f"python3 tools/verify_source_provenance.py --manifest {manifest_ref} "
                    "--source-root <EPHEMERAL_SOURCE_ROOT>"
                ),
            }
        )
    except Exception as exc:
        record.update(
            {
                "verification_status": "failed",
                "error": sanitize_error(str(exc), clone_root),
                "workspace_fixture_verified": False,
                "pinned_source_hashes_verified": False,
            }
        )

    return record


def write_markdown(report: dict[str, Any], output_md: Path) -> None:
    lines = [
        "# First-Party Source Provenance",
        "",
        "This artifact verifies that the first-party source repositories referenced by the",
        "publishable fixtures still match their pinned commits, trees, and source hash",
        "lists when checked out from clean ephemeral clones.",
        "",
        "| Case | Manifest | Status | Commit | Tree | Pinned Files | Boundary |",
        "| --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for case in report["cases"]:
        lines.append(
            "| {case_id} | `{manifest}` | {status} | `{commit}` | `{tree}` | {count} | {boundary} |".format(
                case_id=case["case_id"],
                manifest=case["manifest_ref"],
                status=case["verification_status"],
                commit=case.get("observed_commit", case["expected_commit"])[:12],
                tree=case.get("observed_tree", case["expected_tree"])[:12],
                count=case["pinned_source_hash_count"],
                boundary=case["evidence_scope"],
            )
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This is source-provenance evidence only.",
            "- The full source trees are not vendored into the publishable artifact.",
            "- The real docs-forge Node installer is not executed.",
            "- The full AuditLens product, live connectors, and connector auth flows are not executed.",
            "- No real secrets or public-internet benchmark sinks are introduced by this check.",
        ]
    )
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=REPO_ROOT / "results" / "external" / "first-party-source-provenance.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=REPO_ROOT / "results" / "external" / "first-party-source-provenance.md",
    )
    parser.add_argument(
        "--keep-clones-under",
        type=Path,
        help="Optional debug cache for clones. Do not use for publishable artifacts.",
    )
    args = parser.parse_args(argv)

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)

    if args.keep_clones_under:
        args.keep_clones_under.mkdir(parents=True, exist_ok=True)
        base_dir = args.keep_clones_under.resolve()
        cases = [clone_and_verify(source, base_dir) for source in SOURCES]
    else:
        with tempfile.TemporaryDirectory(prefix="skilldiff-first-party-") as temp:
            base_dir = Path(temp)
            cases = [clone_and_verify(source, base_dir) for source in SOURCES]

    passed = [case for case in cases if case["verification_status"] == "passed"]
    report = {
        "schema_version": "0.1",
        "artifact_id": "first-party-source-provenance",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "evidence_scope": "ephemeral_clean_clone_source_provenance_only",
        "safe_to_publish": True,
        "cases": cases,
        "aggregate": {
            "repositories_checked": len(cases),
            "repositories_verified": len(passed),
            "pinned_source_hashes_verified": sum(
                case["pinned_source_hash_count"]
                for case in passed
                if case.get("pinned_source_hashes_verified") is True
            ),
            "workspace_fixtures_verified": sum(
                1 for case in passed if case.get("workspace_fixture_verified") is True
            ),
            "full_product_workloads_executed": 0,
            "full_source_trees_vendored": 0,
            "real_secrets_present": False,
        },
        "claims_not_supported": [
            "full docs-forge Node installer execution",
            "full AuditLens product execution",
            "live connector auth or SaaS export behavior",
            "runtime drift from the external clone check alone",
        ],
    }

    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, args.output_md)

    if len(passed) != len(cases):
        for case in cases:
            if case["verification_status"] != "passed":
                print(f"{case['case_id']}: {case.get('error', 'verification failed')}", file=sys.stderr)
        return 1

    print(display_path(args.output_json))
    print(display_path(args.output_md))
    return 0


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return "<OUTPUT_OUTSIDE_REPO>"


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
