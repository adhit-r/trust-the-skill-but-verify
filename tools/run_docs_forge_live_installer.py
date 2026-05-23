#!/usr/bin/env python3
"""Run bounded docs-forge live Node CLI installer dry-run checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
MANIFEST_PATH = REPO_ROOT / "benchmark" / "manifests" / "docs-forge-live-installer.json"
EXPECTED_PATH = REPO_ROOT / "benchmark" / "expected" / "docs-forge" / "live-installer-dry-run.json"
TARGET_FIXTURE = REPO_ROOT / "benchmark" / "workspaces" / "docs-forge-live-target"


def run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)


def run_required(args: list[str], cwd: Path) -> str:
    completed = run(args, cwd=cwd)
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(args)}\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return completed.stdout.strip()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_tree(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in {".git", "__pycache__"} for part in rel_parts) or path.name == ".DS_Store":
            continue
        snapshot[path.relative_to(root).as_posix()] = sha256_file(path)
    return snapshot


def changed_paths(before: dict[str, str], after: dict[str, str]) -> list[str]:
    paths = sorted(set(before) | set(after))
    return [path for path in paths if before.get(path) != after.get(path)]


def git_status(source_root: Path) -> str:
    return run_required(["git", "status", "--short"], cwd=source_root)


def verify_source(source_root: Path) -> None:
    completed = subprocess.run(
        [
            PYTHON,
            "tools/verify_source_provenance.py",
            "--manifest",
            "benchmark/manifests/docs-forge-mini.json",
            "--source-root",
            str(source_root),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "docs-forge source provenance verification failed\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )


def sanitize(value: str, *, source_root: Path, temp_root: Path, target_root: Path) -> str:
    return (
        value.replace(str(source_root), "<DOCS_FORGE_SOURCE_ROOT>")
        .replace(str(target_root), "<EPHEMERAL_TARGET>")
        .replace(str(temp_root), "<EPHEMERAL_LIVE_WORKSPACE>")
        .replace(str(REPO_ROOT), "<REPO_ROOT>")
    )


def display_argv(argv: list[str], *, source_root: Path, temp_root: Path, target_root: Path) -> list[str]:
    return [sanitize(arg, source_root=source_root, temp_root=temp_root, target_root=target_root) for arg in argv]


def marker_check(stdout: str, markers: list[str]) -> dict[str, Any]:
    return {
        "required_markers": markers,
        "missing_markers": [marker for marker in markers if marker not in stdout],
    }


def run_case(
    case: dict[str, Any],
    *,
    source_root: Path,
    temp_root: Path,
    target_root: Path,
    markers: list[str],
) -> dict[str, Any]:
    argv = [str(value) for value in case["argv"]]
    argv = [str(target_root) if value == "<EPHEMERAL_TARGET>" else value for value in argv]
    source_before = git_status(source_root)
    target_before = snapshot_tree(target_root)
    completed = run(argv, cwd=source_root)
    source_after = git_status(source_root)
    target_after = snapshot_tree(target_root)
    stdout = sanitize(completed.stdout, source_root=source_root, temp_root=temp_root, target_root=target_root)
    stderr = sanitize(completed.stderr, source_root=source_root, temp_root=temp_root, target_root=target_root)
    marker_result = marker_check(stdout, markers)
    target_changes = changed_paths(target_before, target_after)
    record = {
        "case_id": case["case_id"],
        "argv": display_argv(argv, source_root=source_root, temp_root=temp_root, target_root=target_root),
        "argv_sha256": sha256_text(json.dumps(display_argv(argv, source_root=source_root, temp_root=temp_root, target_root=target_root), sort_keys=True)),
        "dry_run": "--dry-run" in argv,
        "expected_exit_code": case["expected_exit_code"],
        "exit_code": completed.returncode,
        "mutating": case["mutating"],
        "planned_actions": [line for line in stdout.splitlines() if line.startswith("[dry-run]")],
        "source_status_clean_before": source_before == "",
        "source_status_clean_after": source_after == "",
        "stdout_sha256": sha256_text(stdout),
        "stderr_sha256": sha256_text(stderr),
        "stdout_excerpt": stdout[:2000],
        "stderr_excerpt": stderr[:2000],
        "target_changed_files": target_changes,
        "target_mutation_count": len(target_changes),
        **marker_result,
    }
    record["passed"] = (
        record["exit_code"] == record["expected_exit_code"]
        and not record["missing_markers"]
        and record["source_status_clean_before"]
        and record["source_status_clean_after"]
        and record["target_mutation_count"] == 0
    )
    return record


def write_markdown(report: dict[str, Any], output_md: Path) -> None:
    lines = [
        "# docs-forge Live Installer Dry-Run Result",
        "",
        "This artifact records bounded live Node CLI evidence for the pinned docs-forge",
        "source checkout. It exercises help, version, and installer dry-run surfaces",
        "against a disposable synthetic target.",
        "",
        "| Case | Exit | Dry Run | Target Mutations | Missing Markers | Result |",
        "| --- | ---: | --- | ---: | ---: | --- |",
    ]
    for case in report["cases"]:
        lines.append(
            "| {case_id} | {exit_code} | {dry_run} | {mutations} | {missing} | {result} |".format(
                case_id=case["case_id"],
                exit_code=case["exit_code"],
                dry_run="yes" if case["dry_run"] else "no",
                mutations=case["target_mutation_count"],
                missing=len(case["missing_markers"]),
                result="passed" if case["passed"] else "failed",
            )
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This is partial live-installer dry-run evidence, not full product execution.",
            "- It is excluded from MVP runtime-drift counts.",
            "- It does not run `npx`, install packages, modify user home directories, or execute the Codex marketplace command.",
            "- It validates source and target pre/post cleanliness, but it is not complete Node runtime tracing or packet capture.",
        ]
    )
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--output-json", type=Path, default=REPO_ROOT / "results" / "live" / "docs-forge-installer" / "dry_run_result.json")
    parser.add_argument("--output-md", type=Path, default=REPO_ROOT / "results" / "live" / "docs-forge-installer" / "dry_run_report.md")
    args = parser.parse_args(argv)

    source_arg = args.source_root or (Path(os.environ["DOCS_FORGE_SOURCE_ROOT"]) if os.environ.get("DOCS_FORGE_SOURCE_ROOT") else None)
    if source_arg is None:
        raise RuntimeError("DOCS_FORGE_SOURCE_ROOT or --source-root is required for live installer dry-run evidence")
    source_root = source_arg.resolve()
    if not source_root.is_dir():
        raise FileNotFoundError(f"source root does not exist: {source_root}")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
    verify_source(source_root)

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="skilldiff-docs-forge-live-") as temp:
        temp_root = Path(temp)
        target_root = temp_root / "target"
        shutil.copytree(TARGET_FIXTURE, target_root)
        target_fixture_hash = sha256_text(json.dumps(snapshot_tree(target_root), sort_keys=True))

        cases = []
        markers_by_case = expected["required_markers"]
        for case in manifest["commands"]:
            cases.append(
                run_case(
                    case,
                    source_root=source_root,
                    temp_root=temp_root,
                    target_root=target_root,
                    markers=markers_by_case[case["case_id"]],
                )
            )

    passed = [case for case in cases if case["passed"]]
    report = {
        "schema_version": "0.1",
        "artifact_id": "docs-forge-live-installer-dry-run",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "safe_to_publish": True,
        "real_secrets_present": False,
        "excluded_from_mvp_runtime_counts": True,
        "execution_level": "live_node_cli_dry_run",
        "evidence_level": "bounded_help_version_and_installer_dry_run",
        "source_repo": "adhit-r/docs-forge",
        "source_root": "<DOCS_FORGE_SOURCE_ROOT>",
        "source_commit": manifest["source_boundary"]["fixture_source_commit"],
        "source_tree": manifest["source_boundary"]["fixture_source_tree"],
        "contract_ref": manifest["contract_ref"],
        "target_fixture_ref": manifest["target_fixture_ref"],
        "target_fixture_snapshot_sha256": target_fixture_hash,
        "cases": cases,
        "aggregate": {
            "commands_run": len(cases),
            "commands_succeeded": len(passed),
            "dry_run_installer_commands_run": sum(1 for case in cases if case["dry_run"]),
            "target_mutations_observed": sum(case["target_mutation_count"] for case in cases),
            "source_mutations_observed": sum(0 if case["source_status_clean_after"] else 1 for case in cases),
            "non_dry_run_installs_executed": 0,
            "runtime_drift_counts_changed": False,
            "runtime_drift_claims_added": 0,
            "pairwise_disagreements_added": 0,
        },
        "claims_not_supported": [
            "full docs-forge installer execution",
            "npx docs-forge execution",
            "network egress absence under packet capture",
            "complete Node runtime tracing",
            "runtime-drift claims from dry-run evidence",
        ],
    }
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, args.output_md)

    if len(passed) != len(cases):
        failed = ", ".join(case["case_id"] for case in cases if not case["passed"])
        raise RuntimeError(f"docs-forge live installer dry-run failed: {failed}")

    print(args.output_json.resolve().relative_to(REPO_ROOT))
    print(args.output_md.resolve().relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"docs-forge live installer failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
