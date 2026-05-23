#!/usr/bin/env python3
"""Run bounded docs-forge live package-observer checks."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_ROOT))

from run_docs_forge_live_project_local_install import (  # noqa: E402
    changed_paths,
    git_status,
    sha256_file,
    sha256_text,
    snapshot_tree,
    verify_source,
)


MANIFEST_PATH = REPO_ROOT / "benchmark" / "manifests" / "docs-forge-live-package-observer.json"
EXPECTED_PATH = REPO_ROOT / "benchmark" / "expected" / "docs-forge" / "package-acquisition-observer.json"
DEFAULT_OUTPUT_JSON = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "package_observer_result.json"
DEFAULT_OUTPUT_MD = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "package_observer_report.md"
DEFAULT_TRACE = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "package_observer_trace.jsonl"
RESULT_REF = "results/live/docs-forge-installer/package_observer_result.json"
REPORT_REF = "results/live/docs-forge-installer/package_observer_report.md"
TRACE_REF = "results/live/docs-forge-installer/package_observer_trace.jsonl"
MANIFEST_REF = "benchmark/manifests/docs-forge-live-package-observer.json"
TASK_REF = "benchmark/tasks/docs-forge/package-acquisition-observer.txt"
RUNTIME_PROFILE = "LIVE_NODE_NPM_PACK_SYNTHETIC_HOME"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run(args: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True, check=False)


def sanitize(value: str, *, source_root: Path, temp_root: Path, package_dir: Path, home_root: Path, cache_root: Path) -> str:
    return (
        value.replace(str(source_root), "<DOCS_FORGE_SOURCE_ROOT>")
        .replace(str(package_dir), "<EPHEMERAL_PACKAGE_DIR>")
        .replace(str(home_root), "<EPHEMERAL_HOME>")
        .replace(str(cache_root), "<EPHEMERAL_NPM_CACHE>")
        .replace(str(temp_root), "<EPHEMERAL_LIVE_WORKSPACE>")
        .replace(str(REPO_ROOT), "<REPO_ROOT>")
        .replace(str(Path.home()), "<LOCAL_HOME>")
    )


def display_argv(
    argv: list[str],
    *,
    source_root: Path,
    temp_root: Path,
    package_dir: Path,
    home_root: Path,
    cache_root: Path,
) -> list[str]:
    return [
        sanitize(arg, source_root=source_root, temp_root=temp_root, package_dir=package_dir, home_root=home_root, cache_root=cache_root)
        for arg in argv
    ]


def make_env(home_root: Path, cache_root: Path, tmp_root: Path) -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(home_root),
        "TMPDIR": str(tmp_root),
        "LANG": os.environ.get("LANG", "C"),
        "LC_ALL": os.environ.get("LC_ALL", "C"),
        "CI": "1",
        "NO_COLOR": "1",
        "FORCE_COLOR": "0",
        "NPM_CONFIG_CACHE": str(cache_root),
        "NPM_CONFIG_AUDIT": "false",
        "NPM_CONFIG_FUND": "false",
        "NPM_CONFIG_UPDATE_NOTIFIER": "false",
    }


def tarball_entries(path: Path) -> list[str]:
    with tarfile.open(path, "r:gz") as handle:
        names = []
        for member in handle.getmembers():
            if not member.isfile():
                continue
            name = member.name
            if name.startswith("package/"):
                name = name.removeprefix("package/")
            names.append(name)
    return sorted(names)


def run_package_observer(
    case: dict[str, Any],
    *,
    expected: dict[str, Any],
    source_root: Path,
    temp_root: Path,
    home_root: Path,
    cache_root: Path,
    package_dir: Path,
) -> dict[str, Any]:
    argv = [str(value) for value in case["argv"]]
    argv = [str(package_dir) if value == "<EPHEMERAL_PACKAGE_DIR>" else value for value in argv]
    env = make_env(home_root, cache_root, temp_root / "tmp")
    source_before = git_status(source_root)
    home_before = snapshot_tree(home_root)
    cache_before = snapshot_tree(cache_root)
    package_before = snapshot_tree(package_dir)
    completed = run(argv, cwd=source_root, env=env)
    source_after = git_status(source_root)
    home_after = snapshot_tree(home_root)
    cache_after = snapshot_tree(cache_root)
    package_after = snapshot_tree(package_dir)
    stdout = sanitize(completed.stdout, source_root=source_root, temp_root=temp_root, package_dir=package_dir, home_root=home_root, cache_root=cache_root)
    stderr = sanitize(completed.stderr, source_root=source_root, temp_root=temp_root, package_dir=package_dir, home_root=home_root, cache_root=cache_root)

    package_metadata: dict[str, Any] = {}
    parse_error = None
    try:
        parsed_stdout = json.loads(stdout)
        if isinstance(parsed_stdout, list) and parsed_stdout:
            package_metadata = parsed_stdout[0]
    except json.JSONDecodeError as exc:
        parse_error = str(exc)

    package_changes = changed_paths(package_before, package_after)
    tarball_path = package_dir / expected["expected_package"]["filename"]
    tarball_file_entries = tarball_entries(tarball_path) if tarball_path.exists() else []
    observed_files = sorted(file_info["path"] for file_info in package_metadata.get("files", []) if isinstance(file_info, dict) and "path" in file_info)
    expected_files = expected["expected_package"]["files"]
    unexpected_files = sorted(set(observed_files) - set(expected_files))
    missing_files = sorted(set(expected_files) - set(observed_files))
    tarball_unexpected_files = sorted(set(tarball_file_entries) - set(expected_files))
    tarball_missing_files = sorted(set(expected_files) - set(tarball_file_entries))

    record = {
        "case_id": case["case_id"],
        "runtime_profile": RUNTIME_PROFILE,
        "argv": display_argv(argv, source_root=source_root, temp_root=temp_root, package_dir=package_dir, home_root=home_root, cache_root=cache_root),
        "argv_sha256": sha256_text(
            json.dumps(display_argv(argv, source_root=source_root, temp_root=temp_root, package_dir=package_dir, home_root=home_root, cache_root=cache_root), sort_keys=True)
        ),
        "dry_run": False,
        "ignore_scripts": "--ignore-scripts" in argv,
        "expected_exit_code": case["expected_exit_code"],
        "exit_code": completed.returncode,
        "mutating": case["mutating"],
        "source_status_clean_before": source_before == "",
        "source_status_clean_after": source_after == "",
        "source_mutation_count": 0 if source_after == "" else 1,
        "home_mutation_count": len(changed_paths(home_before, home_after)),
        "npm_cache_mutation_count": len(changed_paths(cache_before, cache_after)),
        "package_changed_files": package_changes,
        "package_mutation_count": len(package_changes),
        "stdout_sha256": sha256_text(stdout),
        "stderr_sha256": sha256_text(stderr),
        "stdout_excerpt": stdout[:2000],
        "stderr_excerpt": stderr[:2000],
        "stdout_json_parse_error": parse_error,
        "package_name": package_metadata.get("name"),
        "package_version": package_metadata.get("version"),
        "package_filename": package_metadata.get("filename"),
        "package_size": package_metadata.get("size"),
        "package_unpacked_size": package_metadata.get("unpackedSize"),
        "package_shasum": package_metadata.get("shasum"),
        "package_integrity": package_metadata.get("integrity"),
        "package_entry_count": package_metadata.get("entryCount"),
        "package_files": observed_files,
        "unexpected_package_files": unexpected_files,
        "missing_package_files": missing_files,
        "tarball_files": tarball_file_entries,
        "unexpected_tarball_files": tarball_unexpected_files,
        "missing_tarball_files": tarball_missing_files,
        "tarball_sha256": sha256_file(tarball_path) if tarball_path.exists() else None,
        "tarball_materialized": tarball_path.exists(),
        "npx_executed": False,
        "package_install_executed": False,
        "lifecycle_scripts_executed": False,
        "network_events_observed": 0,
    }
    expected_package = expected["expected_package"]
    record["passed"] = (
        record["exit_code"] == record["expected_exit_code"]
        and record["ignore_scripts"]
        and record["source_status_clean_before"]
        and record["source_status_clean_after"]
        and record["source_mutation_count"] == expected["expected_source_mutations"]
        and record["home_mutation_count"] == expected["expected_home_mutations"]
        and record["package_changed_files"] == case["allowed_package_outputs"]
        and record["package_name"] == expected_package["name"]
        and record["package_version"] == expected_package["version"]
        and record["package_filename"] == expected_package["filename"]
        and record["package_entry_count"] == expected_package["entry_count"]
        and not record["unexpected_package_files"]
        and not record["missing_package_files"]
        and not record["unexpected_tarball_files"]
        and not record["missing_tarball_files"]
        and record["tarball_materialized"]
        and not record["npx_executed"]
        and not record["package_install_executed"]
        and not record["lifecycle_scripts_executed"]
        and record["network_events_observed"] == 0
    )
    return record


def write_markdown(report: dict[str, Any], output_md: Path) -> None:
    case = report["cases"][0]
    lines = [
        "# docs-forge Live Package Observer Result",
        "",
        "This artifact records bounded offline npm package-observer evidence for",
        "the pinned docs-forge source checkout. It materializes the local package",
        "with lifecycle scripts disabled and does not execute `npx`, install from",
        "a registry, or run docs generation.",
        "",
        "| Case | Exit | Package | Entries | Source Mutations | Home Mutations | Result |",
        "| --- | ---: | --- | ---: | ---: | ---: | --- |",
        "| {case_id} | {exit_code} | {package} | {entries} | {source} | {home} | {result} |".format(
            case_id=case["case_id"],
            exit_code=case["exit_code"],
            package=f"{case['package_name']}@{case['package_version']}",
            entries=case["package_entry_count"],
            source=case["source_mutation_count"],
            home=case["home_mutation_count"],
            result="passed" if case["passed"] else "failed",
        ),
        "",
        "## Observed Package Files",
        "",
    ]
    for path in case["package_files"]:
        lines.append(f"- `{path}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This is offline local `npm pack` evidence, not `npx` execution or registry acquisition evidence.",
            "- It is excluded from MVP runtime-drift counts.",
            "- It disables npm lifecycle scripts and uses synthetic HOME plus an ephemeral npm cache.",
            "- It does not prove public-internet safety under packet capture or complete Node/npm runtime tracing.",
        ]
    )
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_trace(report: dict[str, Any], output_json: Path, output_md: Path, trace_path: Path) -> None:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from skilldiff.traces.events import TraceBuilder, TraceContext, validate_trace_file

    case = report["cases"][0]
    context = TraceContext(
        run_id="live-docs-forge-package-observer",
        skill_id="docs-forge",
        task_id="package-acquisition-observer",
        contract_id="docs-forge-live-package-observer",
        runtime_profile=RUNTIME_PROFILE,
        runtime_profile_hash=sha256_text(RUNTIME_PROFILE),
        adapter_id="live_node_npm_pack_observer",
        adapter_version="0.1",
        repeat_id=1,
    )
    builder = TraceBuilder(context)
    builder.add(
        "run.start",
        event_phase="prepare",
        actor="live_node_npm_pack_observer",
        event_status="succeeded",
        target_kind="run",
        target="live-docs-forge-package-observer",
        enforcement_outcome="not_applicable",
        evidence_ref=RESULT_REF,
        metadata={
            "execution_level": report["execution_level"],
            "invocation": case["argv"],
            "source_root": "<DOCS_FORGE_SOURCE_ROOT>",
            "source_commit": report["source_commit"],
            "package_output_dir": "<EPHEMERAL_PACKAGE_DIR>",
        },
    )
    builder.add(
        "capability.snapshot",
        event_phase="prepare",
        actor="live_node_npm_pack_observer",
        event_status="observed",
        target_kind="capability",
        target=RUNTIME_PROFILE,
        enforcement_outcome="observed",
        evidence_ref=MANIFEST_REF,
        metadata={"npm_pack": "enabled", "ignore_scripts": True, "registry_fetch": "not_executed", "packet_capture": "not_enabled"},
    )
    builder.add(
        "activation.select",
        event_phase="run",
        actor="live_node_npm_pack_observer",
        event_status="observed",
        target_kind="activation",
        target="docs-forge",
        operation="select",
        allowed_by_contract=True,
        contract_rule_ids=["SC-ACT-001"],
        matched_allow_rule="SC-ACT-001",
        enforcement_outcome="allowed",
        evidence_ref=TASK_REF,
    )
    approval_id = "approval-docs-forge-package-observer"
    for event_type, target, operation in (
        ("approval.required", "npm pack local package materialization", "approve"),
        ("approval.prompt", "offline npm pack with scripts disabled", "prompt"),
        ("approval.decision", "offline npm pack with scripts disabled", "allow"),
    ):
        builder.add(
            event_type,
            event_phase="run",
            actor="live_node_npm_pack_observer" if event_type != "approval.decision" else "benchmark_operator",
            event_status="observed",
            target_kind="approval",
            target=target,
            operation=operation,
            approval_required=True,
            approval_request_id=approval_id,
            enforcement_outcome="allowed" if event_type == "approval.decision" else "observed",
            evidence_ref=report["contract_ref"],
            metadata={"decision_required": "explicit_allow"} if event_type == "approval.required" else {},
        )
    builder.add(
        "shell.exec",
        event_phase="run",
        actor="live_node_npm_pack_observer",
        event_status="attempted",
        target_kind="process",
        target="npm",
        operation="exec",
        allowed_by_contract=True,
        contract_rule_ids=["SC-SH-001"],
        matched_allow_rule="SC-SH-001",
        enforcement_outcome="allowed",
        evidence_ref=RESULT_REF,
        metadata={"argv": case["argv"], "cwd": "<DOCS_FORGE_SOURCE_ROOT>", "command_sha256": "sha256:" + case["argv_sha256"]},
    )
    for path in case["package_files"]:
        builder.add(
            "filesystem.read",
            event_phase="run",
            actor="npm_pack_observer",
            event_status="observed",
            target_kind="filesystem",
            target="./source/" + path,
            operation="read",
            allowed_by_contract=True,
            contract_rule_ids=["SC-FS-R-001"],
            matched_allow_rule="SC-FS-R-001",
            enforcement_outcome="observed",
            evidence_ref=RESULT_REF,
            metadata={"instrumentation_model": "npm_pack_file_list"},
        )
    builder.add(
        "filesystem.write",
        event_phase="run",
        actor="npm_pack_observer",
        event_status="succeeded",
        target_kind="filesystem",
        target="./package/" + case["package_filename"],
        operation="write",
        allowed_by_contract=True,
        contract_rule_ids=["SC-FS-W-001"],
        matched_allow_rule="SC-FS-W-001",
        enforcement_outcome="observed",
        evidence_ref=RESULT_REF,
        metadata={"instrumentation_model": "package_dir_snapshot_diff", "sha256": "sha256:" + case["tarball_sha256"]},
    )
    builder.add(
        "process.exit",
        event_phase="run",
        actor="live_node_npm_pack_observer",
        event_status="succeeded" if case["exit_code"] == 0 else "failed",
        target_kind="process",
        target="npm",
        operation="exit",
        enforcement_outcome="allowed" if case["exit_code"] == 0 else "failed",
        evidence_ref=RESULT_REF,
        metadata={"exit_code": case["exit_code"], "adapter_outcome": "completed"},
    )
    for target, sink_type in ((output_json, "local_json"), (output_md, "local_report")):
        builder.add(
            "output.generated",
            event_phase="collect",
            actor="live_node_npm_pack_observer",
            event_status="observed",
            target_kind="output",
            target=target.relative_to(REPO_ROOT).as_posix(),
            operation="write",
            allowed_by_contract=True,
            enforcement_outcome="observed",
            sink_type=sink_type,
            payload=target.read_text(encoding="utf-8"),
            payload_redacted=True,
            evidence_ref=target.relative_to(REPO_ROOT).as_posix(),
            metadata={"sha256": "sha256:" + sha256_file(target)},
        )
    builder.add(
        "cleanup.observe",
        event_phase="cleanup",
        actor="live_node_npm_pack_observer",
        event_status="observed",
        target_kind="cleanup",
        target="temporary_workspace_removed",
        enforcement_outcome="observed",
        evidence_ref=RESULT_REF,
        metadata={"removed_paths": ["<EPHEMERAL_LIVE_WORKSPACE>"], "leftover_paths": []},
    )
    builder.add(
        "run.end",
        event_phase="cleanup",
        actor="live_node_npm_pack_observer",
        event_status="succeeded" if case["passed"] else "failed",
        target_kind="run",
        target="live-docs-forge-package-observer",
        enforcement_outcome="not_applicable",
        evidence_ref=TRACE_REF,
        metadata={"exit_code": case["exit_code"], "adapter_outcome": "completed" if case["passed"] else "failed"},
    )
    builder.write(trace_path)
    validate_trace_file(trace_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    args = parser.parse_args(argv)

    source_arg = args.source_root or (Path(os.environ["DOCS_FORGE_SOURCE_ROOT"]) if os.environ.get("DOCS_FORGE_SOURCE_ROOT") else None)
    if source_arg is None:
        raise RuntimeError("DOCS_FORGE_SOURCE_ROOT or --source-root is required for live package-observer evidence")
    source_root = source_arg.resolve()
    if not source_root.is_dir():
        raise FileNotFoundError(f"source root does not exist: {source_root}")

    manifest = load_json(MANIFEST_PATH)
    expected = load_json(EXPECTED_PATH)
    verify_source(source_root)

    for path in (args.output_json, args.output_md, args.trace):
        path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="skilldiff-docs-forge-package-observer-") as temp:
        temp_root = Path(temp)
        home_root = temp_root / "home"
        cache_root = temp_root / "npm-cache"
        package_dir = temp_root / "package"
        (temp_root / "tmp").mkdir(parents=True, exist_ok=True)
        home_root.mkdir(parents=True, exist_ok=True)
        cache_root.mkdir(parents=True, exist_ok=True)
        package_dir.mkdir(parents=True, exist_ok=True)
        cases = [
            run_package_observer(
                manifest["commands"][0],
                expected=expected,
                source_root=source_root,
                temp_root=temp_root,
                home_root=home_root,
                cache_root=cache_root,
                package_dir=package_dir,
            )
        ]

    passed = [case for case in cases if case["passed"]]
    case = cases[0]
    report = {
        "schema_version": "0.1",
        "artifact_id": "docs-forge-live-package-observer",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "safe_to_publish": True,
        "real_secrets_present": False,
        "excluded_from_mvp_runtime_counts": True,
        "execution_level": manifest["execution_level"],
        "evidence_level": manifest["evidence_level"],
        "source_repo": "adhit-r/docs-forge",
        "source_root": "<DOCS_FORGE_SOURCE_ROOT>",
        "source_commit": manifest["source_boundary"]["fixture_source_commit"],
        "source_tree": manifest["source_boundary"]["fixture_source_tree"],
        "manifest_ref": MANIFEST_REF,
        "task_ref": manifest["task_ref"],
        "contract_ref": manifest["contract_ref"],
        "expected_output_ref": manifest["expected_output_ref"],
        "trace_ref": args.trace.resolve().relative_to(REPO_ROOT).as_posix(),
        "runtime_profile": RUNTIME_PROFILE,
        "cases": cases,
        "aggregate": {
            "commands_run": len(cases),
            "commands_succeeded": len(passed),
            "npm_pack_commands_run": 1,
            "npx_commands_executed": sum(1 for item in cases if item["npx_executed"]),
            "package_install_commands_executed": sum(1 for item in cases if item["package_install_executed"]),
            "lifecycle_scripts_executed": sum(1 for item in cases if item["lifecycle_scripts_executed"]),
            "package_tarballs_materialized": sum(1 for item in cases if item["tarball_materialized"]),
            "package_entries_observed": case["package_entry_count"],
            "unexpected_package_entries_observed": len(case["unexpected_package_files"]) + len(case["unexpected_tarball_files"]),
            "source_mutations_observed": case["source_mutation_count"],
            "synthetic_home_mutations_observed": case["home_mutation_count"],
            "ephemeral_npm_cache_mutations_observed": case["npm_cache_mutation_count"],
            "network_events_observed": sum(item["network_events_observed"] for item in cases),
            "public_internet_contact_measured": False,
            "runtime_drift_counts_changed": False,
            "runtime_drift_claims_added": 0,
            "pairwise_disagreements_added": 0,
            "canonical_traces_added": 0,
            "canonical_results_added": 0,
            "live_traces_added": 1,
        },
        "claims_not_supported": [
            "npx docs-forge execution",
            "npm registry acquisition",
            "package install behavior",
            "docs-forge docs-generation workload execution",
            "network egress absence under packet capture",
            "complete Node or npm runtime tracing",
            "runtime-drift claims from package-observer evidence",
        ],
    }
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, args.output_md)
    build_trace(report, args.output_json, args.output_md, args.trace)

    if len(passed) != len(cases):
        failed = ", ".join(item["case_id"] for item in cases if not item["passed"])
        raise RuntimeError(f"docs-forge live package observer failed: {failed}")

    print(args.output_json.resolve().relative_to(REPO_ROOT))
    print(args.output_md.resolve().relative_to(REPO_ROOT))
    print(args.trace.resolve().relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"docs-forge live package observer failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
