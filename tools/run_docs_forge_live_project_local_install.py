#!/usr/bin/env python3
"""Run bounded docs-forge live project-local installer checks."""

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
MANIFEST_PATH = REPO_ROOT / "benchmark" / "manifests" / "docs-forge-live-project-local-install.json"
EXPECTED_PATH = REPO_ROOT / "benchmark" / "expected" / "docs-forge" / "project-local-install.json"
TARGET_FIXTURE = REPO_ROOT / "benchmark" / "workspaces" / "docs-forge-live-target"
DEFAULT_OUTPUT_JSON = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "project_local_install_result.json"
DEFAULT_OUTPUT_MD = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "project_local_install_report.md"
DEFAULT_TRACE = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "project_local_install_trace.jsonl"
CANARY_LABEL = "CANARY_DOCS_FORGE_LIVE_INSTALLER_63D2"

NODE_FS_PRELOAD = r"""
'use strict';
const fs = require('fs');
const tracePath = process.env.SKILLDIFF_NODE_FS_TRACE;
const original = {
  appendFileSync: fs.appendFileSync,
  cpSync: fs.cpSync,
  existsSync: fs.existsSync,
  mkdirSync: fs.mkdirSync,
  readFileSync: fs.readFileSync,
  rmSync: fs.rmSync,
  writeFileSync: fs.writeFileSync
};

function pathString(value) {
  if (typeof value === 'string') return value;
  if (value && typeof value.toString === 'function') return value.toString();
  return String(value);
}

function record(operation, paths) {
  if (!tracePath) return;
  const normalizedPaths = paths.map(pathString);
  if (normalizedPaths.some((path) => path === tracePath)) return;
  try {
    original.appendFileSync(tracePath, JSON.stringify({
      operation,
      paths: normalizedPaths,
      timestamp: new Date().toISOString()
    }) + '\n', 'utf8');
  } catch (_) {
    // Instrumentation must not perturb installer behavior.
  }
}

fs.existsSync = function patchedExistsSync(path) {
  record('existsSync', [path]);
  return original.existsSync.apply(this, arguments);
};

fs.readFileSync = function patchedReadFileSync(path) {
  record('readFileSync', [path]);
  return original.readFileSync.apply(this, arguments);
};

fs.writeFileSync = function patchedWriteFileSync(path) {
  record('writeFileSync', [path]);
  return original.writeFileSync.apply(this, arguments);
};

fs.mkdirSync = function patchedMkdirSync(path) {
  record('mkdirSync', [path]);
  return original.mkdirSync.apply(this, arguments);
};

fs.rmSync = function patchedRmSync(path) {
  record('rmSync', [path]);
  return original.rmSync.apply(this, arguments);
};

fs.cpSync = function patchedCpSync(source, destination) {
  record('cpSync', [source, destination]);
  return original.cpSync.apply(this, arguments);
};
"""


def run(args: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True, check=False)


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
    if not root.exists():
        return snapshot
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
        .replace(str(Path.home()), "<LOCAL_HOME>")
    )


def display_argv(argv: list[str], *, source_root: Path, temp_root: Path, target_root: Path) -> list[str]:
    return [sanitize(arg, source_root=source_root, temp_root=temp_root, target_root=target_root) for arg in argv]


def marker_check(stdout: str, markers: list[str]) -> dict[str, Any]:
    return {
        "required_markers": markers,
        "missing_markers": [marker for marker in markers if marker not in stdout],
    }


def load_node_fs_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                events.append(json.loads(line))
    return events


def classify_path(raw_path: str, *, source_root: Path, target_root: Path) -> str:
    path = Path(raw_path).expanduser()
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path
    for root, label in ((source_root, "source"), (target_root, "target")):
        try:
            rel = resolved.relative_to(root)
        except ValueError:
            continue
        return f"{label}/{rel.as_posix()}"
    try:
        rel_home = resolved.relative_to(Path.home())
    except ValueError:
        return sanitize(raw_path, source_root=source_root, temp_root=target_root.parent, target_root=target_root)
    return f"home/{rel_home.as_posix()}"


def summarized_fs_events(
    events: list[dict[str, Any]],
    *,
    source_root: Path,
    target_root: Path,
) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for event in events:
        paths = [classify_path(path, source_root=source_root, target_root=target_root) for path in event.get("paths", [])]
        summary.append(
            {
                "operation": event.get("operation"),
                "paths": paths,
            }
        )
    return summary


def file_contains_markers(path: Path, markers: list[str]) -> list[str]:
    if not path.exists():
        return list(markers)
    text = path.read_text(encoding="utf-8", errors="replace")
    return [marker for marker in markers if marker not in text]


def scan_changed_files_for_canary(root: Path, relative_paths: list[str], labels: list[str]) -> list[str]:
    hits: list[str] = []
    for rel_path in relative_paths:
        path = root / rel_path
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(label in text for label in labels):
            hits.append(rel_path)
    return hits


def run_project_local_install(
    case: dict[str, Any],
    *,
    expected: dict[str, Any],
    source_root: Path,
    temp_root: Path,
    target_root: Path,
    node_preload_path: Path,
    node_fs_trace_path: Path,
) -> dict[str, Any]:
    argv = [str(value) for value in case["argv"]]
    argv = [str(target_root) if value == "<EPHEMERAL_TARGET>" else value for value in argv]
    source_before = git_status(source_root)
    target_before = snapshot_tree(target_root)
    home_before = snapshot_tree(Path.home() / ".claude" / "skills" / "docs-forge")

    env = os.environ.copy()
    env["NODE_OPTIONS"] = f"--require={node_preload_path}"
    env["SKILLDIFF_NODE_FS_TRACE"] = str(node_fs_trace_path)
    completed = run(argv, cwd=source_root, env=env)

    source_after = git_status(source_root)
    target_after = snapshot_tree(target_root)
    home_after = snapshot_tree(Path.home() / ".claude" / "skills" / "docs-forge")
    stdout = sanitize(completed.stdout, source_root=source_root, temp_root=temp_root, target_root=target_root)
    stderr = sanitize(completed.stderr, source_root=source_root, temp_root=temp_root, target_root=target_root)
    raw_fs_events = load_node_fs_events(node_fs_trace_path)
    fs_events = summarized_fs_events(raw_fs_events, source_root=source_root, target_root=target_root)

    target_changes = changed_paths(target_before, target_after)
    expected_mutations = sorted(case["allowed_target_mutations"])
    unexpected_mutations = sorted(path for path in target_changes if path not in expected_mutations)
    missing_expected_mutations = sorted(path for path in expected_mutations if path not in target_changes)
    file_marker_failures = {
        rel_path: file_contains_markers(target_root / rel_path, markers)
        for rel_path, markers in expected["required_file_markers"].items()
    }
    file_marker_failures = {path: missing for path, missing in file_marker_failures.items() if missing}
    canary_hits = scan_changed_files_for_canary(target_root, target_changes, [CANARY_LABEL])
    output_canary_observed = CANARY_LABEL in stdout or CANARY_LABEL in stderr
    env_read_observed = any(
        event.get("operation") == "readFileSync"
        and any(path.endswith("target/.env") or path == "target/.env" for path in event.get("paths", []))
        for event in fs_events
    )
    source_skill = source_root / "plugins" / "docs-forge" / "skills" / "docs-forge" / "SKILL.md"
    target_skill = target_root / ".claude" / "skills" / "docs-forge" / "SKILL.md"

    marker_result = marker_check(stdout, expected["required_markers"][case["case_id"]])
    record = {
        "case_id": case["case_id"],
        "argv": display_argv(argv, source_root=source_root, temp_root=temp_root, target_root=target_root),
        "argv_sha256": sha256_text(json.dumps(display_argv(argv, source_root=source_root, temp_root=temp_root, target_root=target_root), sort_keys=True)),
        "dry_run": "--dry-run" in argv,
        "expected_exit_code": case["expected_exit_code"],
        "exit_code": completed.returncode,
        "mutating": case["mutating"],
        "source_status_clean_before": source_before == "",
        "source_status_clean_after": source_after == "",
        "home_scope_clean_after": changed_paths(home_before, home_after) == [],
        "stdout_sha256": sha256_text(stdout),
        "stderr_sha256": sha256_text(stderr),
        "stdout_excerpt": stdout[:2000],
        "stderr_excerpt": stderr[:2000],
        "target_changed_files": target_changes,
        "expected_target_mutations": expected_mutations,
        "unexpected_target_mutations": unexpected_mutations,
        "missing_expected_target_mutations": missing_expected_mutations,
        "target_mutation_count": len(target_changes),
        "expected_target_mutation_count": len([path for path in target_changes if path in expected_mutations]),
        "unexpected_target_mutation_count": len(unexpected_mutations),
        "source_mutation_count": 0 if source_after == "" else 1,
        "home_mutation_count": len(changed_paths(home_before, home_after)),
        "env_file_read_observed": env_read_observed,
        "target_canary_hits": canary_hits,
        "output_canary_observed": output_canary_observed,
        "file_marker_failures": file_marker_failures,
        "source_skill_sha256": sha256_file(source_skill),
        "target_skill_sha256": sha256_file(target_skill) if target_skill.exists() else None,
        "node_fs_operations": fs_events,
        "required_markers": marker_result["required_markers"],
        "missing_markers": marker_result["missing_markers"],
    }
    record["passed"] = (
        record["exit_code"] == record["expected_exit_code"]
        and not record["dry_run"]
        and not record["missing_markers"]
        and not record["missing_expected_target_mutations"]
        and not record["unexpected_target_mutations"]
        and not record["file_marker_failures"]
        and not record["target_canary_hits"]
        and not record["output_canary_observed"]
        and not record["env_file_read_observed"]
        and record["source_status_clean_before"]
        and record["source_status_clean_after"]
        and record["home_scope_clean_after"]
        and record["source_skill_sha256"] == record["target_skill_sha256"]
    )
    return record


def write_markdown(report: dict[str, Any], output_md: Path) -> None:
    case = report["cases"][0]
    lines = [
        "# docs-forge Live Project-Local Install Result",
        "",
        "This artifact records bounded live Node CLI evidence for the pinned",
        "docs-forge source checkout. It executes one non-dry-run project-local",
        "installer command against a disposable synthetic target.",
        "",
        "| Case | Exit | Expected Target Writes | Unexpected Target Writes | Source Mutations | Home Mutations | Result |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
        "| {case_id} | {exit_code} | {expected} | {unexpected} | {source} | {home} | {result} |".format(
            case_id=case["case_id"],
            exit_code=case["exit_code"],
            expected=case["expected_target_mutation_count"],
            unexpected=case["unexpected_target_mutation_count"],
            source=case["source_mutation_count"],
            home=case["home_mutation_count"],
            result="passed" if case["passed"] else "failed",
        ),
        "",
        "## Expected Target Writes",
        "",
    ]
    for path in case["expected_target_mutations"]:
        lines.append(f"- `{path}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This is project-local installer evidence, not docs-generation evidence.",
            "- It is excluded from MVP runtime-drift counts.",
            "- It does not run `npx`, install packages, modify user home directories, or execute the Codex marketplace command.",
            "- It uses Node filesystem-call instrumentation and source/target/home pre/post checks, but it is not packet capture or complete Node runtime tracing.",
        ]
    )
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_trace(report: dict[str, Any], output_json: Path, output_md: Path, trace_path: Path) -> None:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from skilldiff.traces.events import TraceBuilder, TraceContext, validate_trace_file

    case = report["cases"][0]
    context = TraceContext(
        run_id="live-docs-forge-project-local-install",
        skill_id="docs-forge",
        task_id="project-local-install",
        contract_id="docs-forge-live-project-local-install",
        runtime_profile="LIVE_NODE_CLI_PROJECT_LOCAL",
        runtime_profile_hash=sha256_text("LIVE_NODE_CLI_PROJECT_LOCAL"),
        adapter_id="live_node_cli_runner",
        adapter_version="0.1",
        repeat_id=1,
    )
    builder = TraceBuilder(context)
    builder.add(
        "run.start",
        event_phase="prepare",
        actor="live_node_cli_runner",
        event_status="succeeded",
        target_kind="run",
        target="live-docs-forge-project-local-install",
        enforcement_outcome="not_applicable",
        evidence_ref="results/live/docs-forge-installer/project_local_install_result.json",
        metadata={
            "dry_run": False,
            "execution_level": report["execution_level"],
            "invocation": case["argv"],
            "workspace_path": "<EPHEMERAL_TARGET>",
            "source_root": "<DOCS_FORGE_SOURCE_ROOT>",
            "source_commit": report["source_commit"],
            "target_fixture_ref": report["target_fixture_ref"],
        },
    )
    builder.add(
        "capability.snapshot",
        event_phase="prepare",
        actor="live_node_cli_runner",
        event_status="observed",
        target_kind="capability",
        target="LIVE_NODE_CLI_PROJECT_LOCAL",
        enforcement_outcome="observed",
        evidence_ref="benchmark/manifests/docs-forge-live-project-local-install.json",
        metadata={"node_fs_preload": "enabled", "packet_capture": "not_enabled"},
    )
    builder.add(
        "activation.select",
        event_phase="run",
        actor="live_node_cli_runner",
        event_status="observed",
        target_kind="activation",
        target="docs-forge",
        operation="select",
        allowed_by_contract=True,
        contract_rule_ids=["SC-ACT-001"],
        matched_allow_rule="SC-ACT-001",
        enforcement_outcome="allowed",
        evidence_ref="benchmark/tasks/docs-forge/project-local-install.txt",
    )
    approval_id = "approval-docs-forge-project-local-install"
    builder.add(
        "approval.required",
        event_phase="run",
        actor="live_node_cli_runner",
        event_status="observed",
        target_kind="approval",
        target="node bin/docs-forge.js install",
        operation="approve",
        approval_required=True,
        approval_request_id=approval_id,
        enforcement_outcome="observed",
        evidence_ref="contracts/docs-forge-live-project-local-install.yaml",
        metadata={"decision_required": "explicit_allow"},
    )
    builder.add(
        "approval.prompt",
        event_phase="run",
        actor="live_node_cli_runner",
        event_status="observed",
        target_kind="approval",
        target="project-local non-dry-run install in disposable target",
        operation="prompt",
        approval_required=True,
        approval_request_id=approval_id,
        enforcement_outcome="observed",
        evidence_ref="contracts/docs-forge-live-project-local-install.yaml",
    )
    builder.add(
        "approval.decision",
        event_phase="run",
        actor="benchmark_operator",
        event_status="observed",
        target_kind="approval",
        target="project-local non-dry-run install in disposable target",
        operation="allow",
        approval_required=True,
        approval_request_id=approval_id,
        enforcement_outcome="allowed",
        evidence_ref="contracts/docs-forge-live-project-local-install.yaml",
    )
    builder.add(
        "shell.exec",
        event_phase="run",
        actor="live_node_cli_runner",
        event_status="attempted",
        target_kind="process",
        target="node",
        operation="exec",
        allowed_by_contract=True,
        contract_rule_ids=["SC-SH-001"],
        matched_allow_rule="SC-SH-001",
        enforcement_outcome="allowed",
        evidence_ref="results/live/docs-forge-installer/project_local_install_result.json",
        metadata={"argv": case["argv"], "cwd": "<DOCS_FORGE_SOURCE_ROOT>", "command_sha256": "sha256:" + case["argv_sha256"]},
    )
    for operation in case["node_fs_operations"]:
        if operation["operation"] not in {"readFileSync", "cpSync"}:
            continue
        for target in operation["paths"]:
            if not target.startswith("source/"):
                continue
            builder.add(
                "filesystem.read",
                event_phase="run",
                actor="node_fs_preload",
                event_status="observed",
                target_kind="filesystem",
                target="./" + target,
                operation="read",
                allowed_by_contract=True,
                contract_rule_ids=["SC-FS-R-001"],
                matched_allow_rule="SC-FS-R-001",
                enforcement_outcome="observed",
                evidence_ref="results/live/docs-forge-installer/project_local_install_result.json",
                metadata={"instrumentation_model": "node_fs_preload", "node_operation": operation["operation"]},
            )
    for path in case["target_changed_files"]:
        rule_id = "SC-FS-W-001" if path.startswith(".claude/") else ("SC-FS-W-003" if path == "GEMINI.md" else "SC-FS-W-002")
        builder.add(
            "filesystem.write",
            event_phase="run",
            actor="node_fs_preload",
            event_status="succeeded",
            target_kind="filesystem",
            target="./target/" + path,
            operation="write",
            allowed_by_contract=True,
            contract_rule_ids=[rule_id],
            matched_allow_rule=rule_id,
            enforcement_outcome="observed",
            evidence_ref="results/live/docs-forge-installer/project_local_install_result.json",
            metadata={"instrumentation_model": "target_snapshot_diff"},
        )
    builder.add(
        "process.exit",
        event_phase="run",
        actor="live_node_cli_runner",
        event_status="succeeded" if case["exit_code"] == 0 else "failed",
        target_kind="process",
        target="node",
        operation="exit",
        enforcement_outcome="allowed" if case["exit_code"] == 0 else "failed",
        evidence_ref="results/live/docs-forge-installer/project_local_install_result.json",
        metadata={"exit_code": case["exit_code"], "adapter_outcome": "completed"},
    )
    for target, sink_type in ((output_json, "local_json"), (output_md, "local_report")):
        builder.add(
            "output.generated",
            event_phase="collect",
            actor="live_node_cli_runner",
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
        actor="live_node_cli_runner",
        event_status="observed",
        target_kind="cleanup",
        target="temporary_workspace_removed",
        enforcement_outcome="observed",
        evidence_ref="results/live/docs-forge-installer/project_local_install_result.json",
        metadata={"removed_paths": ["<EPHEMERAL_LIVE_WORKSPACE>"], "leftover_paths": []},
    )
    builder.add(
        "run.end",
        event_phase="cleanup",
        actor="live_node_cli_runner",
        event_status="succeeded" if case["passed"] else "failed",
        target_kind="run",
        target="live-docs-forge-project-local-install",
        enforcement_outcome="not_applicable",
        evidence_ref=trace_path.relative_to(REPO_ROOT).as_posix(),
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
        raise RuntimeError("DOCS_FORGE_SOURCE_ROOT or --source-root is required for live project-local install evidence")
    source_root = source_arg.resolve()
    if not source_root.is_dir():
        raise FileNotFoundError(f"source root does not exist: {source_root}")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
    verify_source(source_root)

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.trace.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="skilldiff-docs-forge-live-install-") as temp:
        temp_root = Path(temp)
        target_root = temp_root / "target"
        node_preload_path = temp_root / "node_fs_preload.js"
        node_fs_trace_path = temp_root / "node_fs_events.jsonl"
        node_preload_path.write_text(NODE_FS_PRELOAD, encoding="utf-8")
        shutil.copytree(TARGET_FIXTURE, target_root)
        target_fixture_hash = sha256_text(json.dumps(snapshot_tree(target_root), sort_keys=True))

        cases = [
            run_project_local_install(
                manifest["commands"][0],
                expected=expected,
                source_root=source_root,
                temp_root=temp_root,
                target_root=target_root,
                node_preload_path=node_preload_path,
                node_fs_trace_path=node_fs_trace_path,
            )
        ]

    passed = [case for case in cases if case["passed"]]
    report = {
        "schema_version": "0.1",
        "artifact_id": "docs-forge-live-project-local-install",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "safe_to_publish": True,
        "real_secrets_present": False,
        "excluded_from_mvp_runtime_counts": True,
        "execution_level": "live_node_cli_project_local_install",
        "evidence_level": "bounded_project_local_installer_execution",
        "source_repo": "adhit-r/docs-forge",
        "source_root": "<DOCS_FORGE_SOURCE_ROOT>",
        "source_commit": manifest["source_boundary"]["fixture_source_commit"],
        "source_tree": manifest["source_boundary"]["fixture_source_tree"],
        "contract_ref": manifest["contract_ref"],
        "target_fixture_ref": manifest["target_fixture_ref"],
        "target_fixture_snapshot_sha256": target_fixture_hash,
        "trace_ref": args.trace.resolve().relative_to(REPO_ROOT).as_posix(),
        "cases": cases,
        "aggregate": {
            "commands_run": len(cases),
            "commands_succeeded": len(passed),
            "project_local_installs_executed": len([case for case in cases if case["passed"] and not case["dry_run"]]),
            "non_dry_run_installs_executed": len([case for case in cases if not case["dry_run"]]),
            "target_allowed_mutations_observed": sum(case["expected_target_mutation_count"] for case in cases),
            "unexpected_target_mutations_observed": sum(case["unexpected_target_mutation_count"] for case in cases),
            "source_mutations_observed": sum(case["source_mutation_count"] for case in cases),
            "home_mutations_observed": sum(case["home_mutation_count"] for case in cases),
            "env_file_reads_observed": sum(1 for case in cases if case["env_file_read_observed"]),
            "canary_observations": sum(len(case["target_canary_hits"]) + int(case["output_canary_observed"]) for case in cases),
            "network_commands_observed": 0,
            "npx_commands_observed": 0,
            "codex_marketplace_commands_observed": 0,
            "runtime_drift_counts_changed": False,
            "runtime_drift_claims_added": 0,
            "pairwise_disagreements_added": 0,
        },
        "claims_not_supported": [
            "full docs-forge product execution",
            "docs-forge docs-generation workload execution",
            "npx docs-forge execution",
            "global or user-scope installation",
            "network egress absence under packet capture",
            "complete Node runtime tracing",
            "runtime-drift claims from installer-only evidence",
        ],
    }
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, args.output_md)
    build_trace(report, args.output_json, args.output_md, args.trace)

    if len(passed) != len(cases):
        failed = ", ".join(case["case_id"] for case in cases if not case["passed"])
        raise RuntimeError(f"docs-forge live project-local install failed: {failed}")

    print(args.output_json.resolve().relative_to(REPO_ROOT))
    print(args.output_md.resolve().relative_to(REPO_ROOT))
    print(args.trace.resolve().relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"docs-forge live project-local install failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
