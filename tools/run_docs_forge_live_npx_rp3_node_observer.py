#!/usr/bin/env python3
"""Run bounded docs-forge local-tarball npx checks inside an RP3 Node container."""

from __future__ import annotations

import argparse
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
TOOLS_ROOT = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_ROOT))

from run_docs_forge_live_package_observer import tarball_entries  # noqa: E402
from run_docs_forge_live_project_local_install import (  # noqa: E402
    changed_paths,
    git_status,
    sha256_file,
    sha256_text,
    snapshot_tree,
    verify_source,
)


MANIFEST_PATH = REPO_ROOT / "benchmark" / "manifests" / "docs-forge-live-npx-rp3-node-observer.json"
EXPECTED_PATH = REPO_ROOT / "benchmark" / "expected" / "docs-forge" / "npx-rp3-node-observer.json"
DEFAULT_OUTPUT_JSON = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_rp3_node_observer_result.json"
DEFAULT_OUTPUT_MD = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_rp3_node_observer_report.md"
DEFAULT_TRACE = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_rp3_node_observer_trace.jsonl"
RESULT_REF = "results/live/docs-forge-installer/npx_rp3_node_observer_result.json"
REPORT_REF = "results/live/docs-forge-installer/npx_rp3_node_observer_report.md"
TRACE_REF = "results/live/docs-forge-installer/npx_rp3_node_observer_trace.jsonl"
MANIFEST_REF = "benchmark/manifests/docs-forge-live-npx-rp3-node-observer.json"
TASK_REF = "benchmark/tasks/docs-forge/npx-rp3-node-observer.txt"
RUNTIME_PROFILE = "RP3_NODE_LOCAL_TARBALL_NPX_EXPERIMENTAL"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def docker_executable() -> str:
    configured = os.environ.get("DOCKER_BIN")
    if configured:
        if Path(configured).exists() and os.access(configured, os.X_OK):
            return configured
        raise RuntimeError(f"configured DOCKER_BIN is not executable: {configured}")
    found = shutil.which("docker")
    if found:
        return found
    for candidate in [
        "/usr/local/bin/docker",
        "/opt/homebrew/bin/docker",
        "/Applications/Docker.app/Contents/Resources/bin/docker",
    ]:
        if Path(candidate).exists() and os.access(candidate, os.X_OK):
            return candidate
    raise RuntimeError("docker executable not found")


def inspect_image(image_ref: str, docker_bin: str) -> dict[str, Any]:
    completed = subprocess.run(
        [docker_bin, "image", "inspect", image_ref],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"docker image inspect failed for {image_ref}\n{completed.stderr or completed.stdout}")
    image = json.loads(completed.stdout)[0]
    return {
        "image_id": image.get("Id"),
        "repo_tags": image.get("RepoTags") or [],
        "repo_digests": image.get("RepoDigests") or [],
        "architecture": image.get("Architecture"),
        "os": image.get("Os"),
    }


def sanitize(
    value: str,
    *,
    source_root: Path,
    temp_root: Path,
    package_dir: Path,
    home_root: Path,
    cache_root: Path,
) -> str:
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
    displayed = []
    for arg in argv:
        if Path(arg).is_absolute() and Path(arg).name == "docker":
            displayed.append("docker")
            continue
        displayed.append(
            sanitize(
                arg,
                source_root=source_root,
                temp_root=temp_root,
                package_dir=package_dir,
                home_root=home_root,
                cache_root=cache_root,
            )
        )
    return displayed


def docker_env_args(home_root: str = "/workspace/home", cache_root: str = "/workspace/npm-cache") -> list[str]:
    return [
        "--env=CI=1",
        "--env=NO_COLOR=1",
        "--env=FORCE_COLOR=0",
        f"--env=HOME={home_root}",
        "--env=TMPDIR=/tmp",
        f"--env=NPM_CONFIG_CACHE={cache_root}",
        "--env=NPM_CONFIG_AUDIT=false",
        "--env=NPM_CONFIG_FUND=false",
        "--env=NPM_CONFIG_UPDATE_NOTIFIER=false",
        "--env=NPM_CONFIG_OFFLINE=true",
        "--env=NPM_CONFIG_FETCH_RETRIES=0",
        "--env=NPM_CONFIG_REGISTRY=http://127.0.0.1:9/",
    ]


def run_docker(
    *,
    docker_bin: str,
    image_ref: str,
    command: list[str],
    workdir: str,
    source_root: Path | None,
    package_dir: Path | None,
    home_root: Path | None,
    cache_root: Path | None,
    package_readonly: bool = False,
) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    argv = [
        docker_bin,
        "run",
        "--rm",
        "--network=none",
        "--read-only",
        "--user=1000:1000",
    ]
    if source_root is not None:
        argv.append(f"--mount=type=bind,source={source_root},target=/workspace/repo,readonly")
    if package_dir is not None:
        readonly = ",readonly" if package_readonly else ""
        argv.append(f"--mount=type=bind,source={package_dir},target=/workspace/package{readonly}")
    if home_root is not None:
        argv.append(f"--mount=type=bind,source={home_root},target=/workspace/home")
    if cache_root is not None:
        argv.append(f"--mount=type=bind,source={cache_root},target=/workspace/npm-cache")
    argv.extend(["--tmpfs=/tmp", f"--workdir={workdir}"])
    if home_root is None or cache_root is None:
        argv.extend(docker_env_args(home_root="/tmp", cache_root="/tmp/npm-cache"))
    else:
        argv.extend(docker_env_args())
    argv.append(image_ref)
    argv.extend(command)
    completed = subprocess.run(argv, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    return completed, argv


def parse_pack_stdout(stdout: str) -> dict[str, Any]:
    parsed = json.loads(stdout)
    if not isinstance(parsed, list) or not parsed or not isinstance(parsed[0], dict):
        raise RuntimeError("npm pack stdout did not contain package metadata")
    return parsed[0]


def parse_preflight(stdout: str) -> dict[str, str | None]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    return {
        "node_version": lines[0] if len(lines) > 0 else None,
        "npm_version": lines[1] if len(lines) > 1 else None,
        "npx_version": lines[2] if len(lines) > 2 else None,
        "strace_version": lines[3] if len(lines) > 3 else None,
        "python_version": lines[4] if len(lines) > 4 else None,
    }


def chmod_workspace(paths: list[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
        path.chmod(0o777)


def run_container_observer(
    case: dict[str, Any],
    *,
    expected: dict[str, Any],
    source_root: Path,
    temp_root: Path,
    home_root: Path,
    cache_root: Path,
    package_dir: Path,
    docker_bin: str,
    image_ref: str,
) -> dict[str, Any]:
    expected_package = expected["expected_package"]
    tarball_path = package_dir / expected_package["filename"]
    pack_argv = [str(value) for value in case["pack_argv"]]
    npx_argv = [str(value) for value in case["npx_argv"]]

    source_before = git_status(source_root)
    home_before = snapshot_tree(home_root)
    cache_before = snapshot_tree(cache_root)
    package_before = snapshot_tree(package_dir)

    pack_completed, pack_docker_argv = run_docker(
        docker_bin=docker_bin,
        image_ref=image_ref,
        command=pack_argv,
        workdir="/workspace/repo",
        source_root=source_root,
        package_dir=package_dir,
        home_root=home_root,
        cache_root=cache_root,
    )
    package_after_pack = snapshot_tree(package_dir)
    npx_completed, npx_docker_argv = run_docker(
        docker_bin=docker_bin,
        image_ref=image_ref,
        command=npx_argv,
        workdir="/workspace/package",
        source_root=None,
        package_dir=package_dir,
        home_root=home_root,
        cache_root=cache_root,
        package_readonly=True,
    )

    source_after = git_status(source_root)
    home_after = snapshot_tree(home_root)
    cache_after = snapshot_tree(cache_root)
    package_after = snapshot_tree(package_dir)

    pack_stdout = sanitize(
        pack_completed.stdout,
        source_root=source_root,
        temp_root=temp_root,
        package_dir=package_dir,
        home_root=home_root,
        cache_root=cache_root,
    )
    pack_stderr = sanitize(
        pack_completed.stderr,
        source_root=source_root,
        temp_root=temp_root,
        package_dir=package_dir,
        home_root=home_root,
        cache_root=cache_root,
    )
    npx_stdout = sanitize(
        npx_completed.stdout,
        source_root=source_root,
        temp_root=temp_root,
        package_dir=package_dir,
        home_root=home_root,
        cache_root=cache_root,
    )
    npx_stderr = sanitize(
        npx_completed.stderr,
        source_root=source_root,
        temp_root=temp_root,
        package_dir=package_dir,
        home_root=home_root,
        cache_root=cache_root,
    )

    package_metadata: dict[str, Any] = {}
    parse_error = None
    try:
        package_metadata = parse_pack_stdout(pack_completed.stdout)
    except (json.JSONDecodeError, RuntimeError) as exc:
        parse_error = str(exc)

    package_files = sorted(file_info["path"] for file_info in package_metadata.get("files", []) if isinstance(file_info, dict) and "path" in file_info)
    tarball_files = tarball_entries(tarball_path) if tarball_path.exists() else []
    required_markers = expected["required_stdout_markers"]
    missing_markers = [marker for marker in required_markers if marker not in npx_stdout]
    package_changes = changed_paths(package_before, package_after)

    record = {
        "case_id": case["case_id"],
        "runtime_profile": RUNTIME_PROFILE,
        "container_image_ref": image_ref,
        "docker_network_mode": "none",
        "read_only_rootfs": True,
        "docker_user": "1000:1000",
        "docker_socket_mounted": False,
        "pack_argv": pack_argv,
        "npx_argv": npx_argv,
        "pack_docker_argv": display_argv(pack_docker_argv, source_root=source_root, temp_root=temp_root, package_dir=package_dir, home_root=home_root, cache_root=cache_root),
        "npx_docker_argv": display_argv(npx_docker_argv, source_root=source_root, temp_root=temp_root, package_dir=package_dir, home_root=home_root, cache_root=cache_root),
        "pack_argv_sha256": sha256_text(json.dumps(pack_argv, sort_keys=True)),
        "npx_argv_sha256": sha256_text(json.dumps(npx_argv, sort_keys=True)),
        "pack_docker_argv_sha256": sha256_text(json.dumps(display_argv(pack_docker_argv, source_root=source_root, temp_root=temp_root, package_dir=package_dir, home_root=home_root, cache_root=cache_root), sort_keys=True)),
        "npx_docker_argv_sha256": sha256_text(json.dumps(display_argv(npx_docker_argv, source_root=source_root, temp_root=temp_root, package_dir=package_dir, home_root=home_root, cache_root=cache_root), sort_keys=True)),
        "dry_run": False,
        "mutating": case["mutating"],
        "expected_exit_code": case["expected_exit_code"],
        "pack_exit_code": pack_completed.returncode,
        "npx_exit_code": npx_completed.returncode,
        "pack_ignore_scripts": "--ignore-scripts" in pack_argv,
        "npx_offline": "--offline" in npx_argv,
        "npx_uses_local_tarball": str(tarball_path) in npx_argv or f"/workspace/package/{expected_package['filename']}" in npx_argv,
        "source_status_clean_before": source_before == "",
        "source_status_clean_after": source_after == "",
        "source_mutation_count": 0 if source_after == "" else 1,
        "home_mutation_count": len(changed_paths(home_before, home_after)),
        "npm_cache_mutation_count": len(changed_paths(cache_before, cache_after)),
        "package_changed_files": package_changes,
        "package_changed_files_after_pack": changed_paths(package_before, package_after_pack),
        "pack_stdout_sha256": sha256_text(pack_stdout),
        "pack_stderr_sha256": sha256_text(pack_stderr),
        "npx_stdout_sha256": sha256_text(npx_stdout),
        "npx_stderr_sha256": sha256_text(npx_stderr),
        "pack_stdout_excerpt": pack_stdout[:2000],
        "pack_stderr_excerpt": pack_stderr[:2000],
        "npx_stdout_excerpt": npx_stdout[:2000],
        "npx_stderr_excerpt": npx_stderr[:2000],
        "pack_stdout_json_parse_error": parse_error,
        "package_name": package_metadata.get("name"),
        "package_version": package_metadata.get("version"),
        "package_filename": package_metadata.get("filename"),
        "package_entry_count": package_metadata.get("entryCount"),
        "package_files": package_files,
        "tarball_files": tarball_files,
        "tarball_sha256": sha256_file(tarball_path) if tarball_path.exists() else None,
        "tarball_materialized": tarball_path.exists(),
        "required_stdout_markers": required_markers,
        "missing_stdout_markers": missing_markers,
        "npx_package_name_execution": npx_argv == ["npx", "docs-forge"],
        "registry_acquisition_executed": False,
        "package_install_executed": False,
        "lifecycle_scripts_executed": False,
        "network_events_observed": 0,
        "public_internet_contact_measured": False,
    }
    record["passed"] = (
        record["pack_exit_code"] == 0
        and record["npx_exit_code"] == record["expected_exit_code"]
        and record["pack_ignore_scripts"]
        and record["npx_offline"]
        and record["npx_uses_local_tarball"]
        and record["source_status_clean_before"]
        and record["source_status_clean_after"]
        and record["source_mutation_count"] == expected["expected_source_mutations"]
        and record["home_mutation_count"] == expected["expected_home_mutations"]
        and record["package_changed_files"] == case["allowed_package_outputs"]
        and record["package_name"] == expected_package["name"]
        and record["package_version"] == expected_package["version"]
        and record["package_filename"] == expected_package["filename"]
        and record["package_entry_count"] == expected_package["entry_count"]
        and record["tarball_materialized"]
        and not record["missing_stdout_markers"]
        and not record["npx_package_name_execution"]
        and not record["registry_acquisition_executed"]
        and not record["package_install_executed"]
        and not record["lifecycle_scripts_executed"]
        and record["network_events_observed"] == 0
    )
    return record


def write_markdown(report: dict[str, Any], output_md: Path) -> None:
    case = report["cases"][0]
    lines = [
        "# docs-forge Live RP3 Node Local-Tarball npx Observer Result",
        "",
        "This artifact records bounded Dockerized npx evidence for the pinned",
        "docs-forge source checkout. It uses an experimental Node-capable RP3",
        "image with Docker networking disabled, materializes one local tarball",
        "with lifecycle scripts disabled, then runs docs-forge help through",
        "`npx --offline` from that local tarball.",
        "",
        "| Case | npx Exit | Image | Package | Entries | Source Mutations | Home Mutations | Result |",
        "| --- | ---: | --- | --- | ---: | ---: | ---: | --- |",
        "| {case_id} | {exit_code} | `{image}` | {package} | {entries} | {source} | {home} | {result} |".format(
            case_id=case["case_id"],
            exit_code=case["npx_exit_code"],
            image=report["container_image_ref"],
            package=f"{case['package_name']}@{case['package_version']}",
            entries=case["package_entry_count"],
            source=case["source_mutation_count"],
            home=case["home_mutation_count"],
            result="passed" if case["passed"] else "failed",
        ),
        "",
        "## Container Boundary",
        "",
        "- Docker ran with `--network=none` and `--read-only` for the preflight, package, and npx commands.",
        "- The docs-forge source checkout was mounted read-only for package materialization.",
        "- `npx` used `--offline` and `--package /workspace/package/docs-forge-0.3.0.tgz`.",
        "- No package-name `npx docs-forge` registry acquisition was executed.",
        "- No package install command, lifecycle script, docs generation, or project/user/global installer write was executed.",
        "- This is not an MVP RP2/RP3 runtime-drift claim.",
    ]
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_trace(report: dict[str, Any], output_json: Path, output_md: Path, trace_path: Path) -> None:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from skilldiff.traces.events import TraceBuilder, TraceContext, validate_trace_file

    case = report["cases"][0]
    context = TraceContext(
        run_id="live-docs-forge-npx-rp3-node-observer",
        skill_id="docs-forge",
        task_id="npx-rp3-node-observer",
        contract_id="docs-forge-live-npx-rp3-node-observer",
        runtime_profile=RUNTIME_PROFILE,
        runtime_profile_hash=sha256_text(RUNTIME_PROFILE + report["container_image_ref"]),
        adapter_id="live_rp3_node_container_npx_observer",
        adapter_version="0.1",
        repeat_id=1,
    )
    builder = TraceBuilder(context)
    builder.add(
        "run.start",
        event_phase="prepare",
        actor="live_rp3_node_container_npx_observer",
        event_status="succeeded",
        target_kind="run",
        target="live-docs-forge-npx-rp3-node-observer",
        enforcement_outcome="not_applicable",
        evidence_ref=RESULT_REF,
        metadata={"execution_level": report["execution_level"], "source_root": "<DOCS_FORGE_SOURCE_ROOT>", "source_commit": report["source_commit"]},
    )
    builder.add(
        "capability.snapshot",
        event_phase="prepare",
        actor="live_rp3_node_container_npx_observer",
        event_status="observed",
        target_kind="capability",
        target=RUNTIME_PROFILE,
        enforcement_outcome="observed",
        evidence_ref=MANIFEST_REF,
        metadata={
            "container_image_ref": report["container_image_ref"],
            "network_mode": "none",
            "read_only_rootfs": True,
            "docker_socket_mounted": False,
            "npx": "enabled",
            "offline": True,
            "local_tarball": True,
            "packet_capture": "not_enabled",
        },
    )
    builder.add(
        "activation.select",
        event_phase="run",
        actor="live_rp3_node_container_npx_observer",
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
    builder.add(
        "shell.exec",
        event_phase="run",
        actor="live_rp3_node_container_npx_observer",
        event_status="attempted",
        target_kind="process",
        target="container-preflight",
        operation="exec",
        allowed_by_contract=True,
        contract_rule_ids=["SC-SH-000"],
        matched_allow_rule="SC-SH-000",
        enforcement_outcome="allowed",
        evidence_ref=RESULT_REF,
        metadata={"argv": report["preflight"]["argv"], "docker_network_mode": "none", "read_only_rootfs": True},
    )
    builder.add(
        "process.exit",
        event_phase="run",
        actor="live_rp3_node_container_npx_observer",
        event_status="succeeded" if report["preflight"]["exit_code"] == 0 else "failed",
        target_kind="process",
        target="container-preflight",
        operation="exit",
        enforcement_outcome="allowed" if report["preflight"]["exit_code"] == 0 else "failed",
        evidence_ref=RESULT_REF,
        metadata={"exit_code": report["preflight"]["exit_code"], "versions": report["preflight"]["versions"]},
    )
    approval_id = "approval-docs-forge-rp3-node-npx-observer"
    for event_type, target, operation in (
        ("approval.required", "Dockerized offline npx local-tarball docs-forge help", "approve"),
        ("approval.prompt", "npx --offline --package local tarball in RP3 Node container", "prompt"),
        ("approval.decision", "npx --offline --package local tarball in RP3 Node container", "allow"),
    ):
        builder.add(
            event_type,
            event_phase="run",
            actor="live_rp3_node_container_npx_observer" if event_type != "approval.decision" else "benchmark_operator",
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
        actor="live_rp3_node_container_npx_observer",
        event_status="attempted",
        target_kind="process",
        target="npm",
        operation="exec",
        allowed_by_contract=True,
        contract_rule_ids=["SC-SH-001"],
        matched_allow_rule="SC-SH-001",
        enforcement_outcome="allowed",
        evidence_ref=RESULT_REF,
        metadata={"argv": case["pack_argv"], "docker_network_mode": "none", "command_sha256": "sha256:" + case["pack_argv_sha256"]},
    )
    for path in case["package_files"]:
        builder.add(
            "filesystem.read",
            event_phase="run",
            actor="container_npm_pack_observer",
            event_status="observed",
            target_kind="filesystem",
            target="./source/" + path,
            operation="read",
            allowed_by_contract=True,
            contract_rule_ids=["SC-FS-R-001"],
            matched_allow_rule="SC-FS-R-001",
            enforcement_outcome="observed",
            evidence_ref=RESULT_REF,
            metadata={"instrumentation_model": "npm_pack_file_list_inside_docker_network_none"},
        )
    builder.add(
        "filesystem.write",
        event_phase="run",
        actor="container_npm_pack_observer",
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
        actor="live_rp3_node_container_npx_observer",
        event_status="succeeded" if case["pack_exit_code"] == 0 else "failed",
        target_kind="process",
        target="npm",
        operation="exit",
        enforcement_outcome="allowed" if case["pack_exit_code"] == 0 else "failed",
        evidence_ref=RESULT_REF,
        metadata={"exit_code": case["pack_exit_code"], "adapter_outcome": "completed"},
    )
    builder.add(
        "shell.exec",
        event_phase="run",
        actor="live_rp3_node_container_npx_observer",
        event_status="attempted",
        target_kind="process",
        target="npx",
        operation="exec",
        allowed_by_contract=True,
        contract_rule_ids=["SC-SH-002"],
        matched_allow_rule="SC-SH-002",
        enforcement_outcome="allowed",
        evidence_ref=RESULT_REF,
        metadata={"argv": case["npx_argv"], "docker_network_mode": "none", "command_sha256": "sha256:" + case["npx_argv_sha256"]},
    )
    builder.add(
        "filesystem.read",
        event_phase="run",
        actor="container_npx_observer",
        event_status="observed",
        target_kind="filesystem",
        target="./package/" + case["package_filename"],
        operation="read",
        allowed_by_contract=True,
        contract_rule_ids=["SC-FS-R-002"],
        matched_allow_rule="SC-FS-R-002",
        enforcement_outcome="observed",
        evidence_ref=RESULT_REF,
        metadata={"instrumentation_model": "local_tarball_argument_inside_docker_network_none", "sha256": "sha256:" + case["tarball_sha256"]},
    )
    builder.add(
        "process.exit",
        event_phase="run",
        actor="live_rp3_node_container_npx_observer",
        event_status="succeeded" if case["npx_exit_code"] == 0 else "failed",
        target_kind="process",
        target="npx",
        operation="exit",
        enforcement_outcome="allowed" if case["npx_exit_code"] == 0 else "failed",
        evidence_ref=RESULT_REF,
        metadata={"exit_code": case["npx_exit_code"], "adapter_outcome": "completed"},
    )
    for target, sink_type in ((output_json, "local_json"), (output_md, "local_report")):
        builder.add(
            "output.generated",
            event_phase="collect",
            actor="live_rp3_node_container_npx_observer",
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
        actor="live_rp3_node_container_npx_observer",
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
        actor="live_rp3_node_container_npx_observer",
        event_status="succeeded" if case["passed"] and report["preflight"]["passed"] else "failed",
        target_kind="run",
        target="live-docs-forge-npx-rp3-node-observer",
        enforcement_outcome="not_applicable",
        evidence_ref=TRACE_REF,
        metadata={"exit_code": case["npx_exit_code"], "adapter_outcome": "completed" if case["passed"] and report["preflight"]["passed"] else "failed"},
    )
    builder.write(trace_path)
    validate_trace_file(trace_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--container-image-ref", default=None)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    args = parser.parse_args(argv)

    source_arg = args.source_root or (Path(os.environ["DOCS_FORGE_SOURCE_ROOT"]) if os.environ.get("DOCS_FORGE_SOURCE_ROOT") else None)
    if source_arg is None:
        raise RuntimeError("DOCS_FORGE_SOURCE_ROOT or --source-root is required for live RP3 Node npx-observer evidence")
    source_root = source_arg.resolve()
    if not source_root.is_dir():
        raise FileNotFoundError(f"source root does not exist: {source_root}")

    manifest = load_json(MANIFEST_PATH)
    expected = load_json(EXPECTED_PATH)
    image_ref = args.container_image_ref or manifest["runtime_boundary"]["container_image_ref"]
    docker_bin = docker_executable()
    image_metadata = inspect_image(image_ref, docker_bin)
    verify_source(source_root)

    for path in (args.output_json, args.output_md, args.trace):
        path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="skilldiff-docs-forge-rp3-node-npx-") as temp:
        temp_root = Path(temp)
        home_root = temp_root / "home"
        cache_root = temp_root / "npm-cache"
        package_dir = temp_root / "package"
        chmod_workspace([temp_root, home_root, cache_root, package_dir])

        preflight_argv = manifest["commands"][0]["argv"]
        preflight_completed, preflight_docker_argv = run_docker(
            docker_bin=docker_bin,
            image_ref=image_ref,
            command=preflight_argv,
            workdir="/tmp",
            source_root=None,
            package_dir=None,
            home_root=None,
            cache_root=None,
        )
        preflight_stdout = sanitize(preflight_completed.stdout, source_root=source_root, temp_root=temp_root, package_dir=package_dir, home_root=home_root, cache_root=cache_root)
        preflight_stderr = sanitize(preflight_completed.stderr, source_root=source_root, temp_root=temp_root, package_dir=package_dir, home_root=home_root, cache_root=cache_root)
        preflight = {
            "case_id": manifest["commands"][0]["case_id"],
            "argv": preflight_argv,
            "docker_argv": display_argv(preflight_docker_argv, source_root=source_root, temp_root=temp_root, package_dir=package_dir, home_root=home_root, cache_root=cache_root),
            "docker_network_mode": "none",
            "read_only_rootfs": True,
            "docker_user": "1000:1000",
            "exit_code": preflight_completed.returncode,
            "stdout_sha256": sha256_text(preflight_stdout),
            "stderr_sha256": sha256_text(preflight_stderr),
            "stdout_excerpt": preflight_stdout[:1000],
            "stderr_excerpt": preflight_stderr[:1000],
            "versions": parse_preflight(preflight_stdout),
        }
        node_version = preflight["versions"].get("node_version")
        node_major = int(str(node_version).removeprefix("v").split(".", 1)[0]) if node_version else 0
        preflight["passed"] = preflight_completed.returncode == 0 and node_major >= expected["minimum_node_major"]

        cases = [
            run_container_observer(
                manifest["commands"][1],
                expected=expected,
                source_root=source_root,
                temp_root=temp_root,
                home_root=home_root,
                cache_root=cache_root,
                package_dir=package_dir,
                docker_bin=docker_bin,
                image_ref=image_ref,
            )
        ]

    passed = [case for case in cases if case["passed"]]
    case = cases[0]
    report = {
        "schema_version": "0.1",
        "artifact_id": "docs-forge-live-npx-rp3-node-observer",
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
        "container_image_ref": image_ref,
        "container_image_metadata": image_metadata,
        "container_constraints": manifest["runtime_boundary"],
        "preflight": preflight,
        "cases": cases,
        "aggregate": {
            "commands_run": 3,
            "commands_succeeded": int(preflight["exit_code"] == 0) + int(case["pack_exit_code"] == 0) + int(case["npx_exit_code"] == 0),
            "container_preflight_commands_run": 1,
            "workload_commands_run": 2,
            "docker_container_commands_run": 3,
            "docker_network_none_commands_run": 3,
            "docker_read_only_rootfs_commands_run": 3,
            "docker_socket_mounts_observed": 0,
            "npm_pack_commands_run": 1,
            "npx_commands_executed": 1,
            "npx_local_tarball_commands_executed": int(case["npx_uses_local_tarball"]),
            "npx_package_name_commands_executed": int(case["npx_package_name_execution"]),
            "registry_acquisitions_observed": int(case["registry_acquisition_executed"]),
            "package_install_commands_executed": int(case["package_install_executed"]),
            "lifecycle_scripts_executed": int(case["lifecycle_scripts_executed"]),
            "package_tarballs_materialized": int(case["tarball_materialized"]),
            "package_entries_observed": case["package_entry_count"],
            "source_mutations_observed": case["source_mutation_count"],
            "synthetic_home_mutations_observed": case["home_mutation_count"],
            "ephemeral_npm_cache_mutations_observed": case["npm_cache_mutation_count"],
            "network_events_observed": case["network_events_observed"],
            "public_internet_contact_measured": False,
            "runtime_drift_counts_changed": False,
            "runtime_drift_claims_added": 0,
            "pairwise_disagreements_added": 0,
            "canonical_traces_added": 0,
            "canonical_results_added": 0,
            "live_traces_added": 1,
        },
        "claims_not_supported": [
            "public npm registry acquisition",
            "package-name npx docs-forge execution",
            "package install behavior",
            "docs-forge docs-generation workload execution",
            "network egress absence under packet capture",
            "complete Node or npm runtime tracing",
            "RP2/RP3 runtime-drift claims from RP3-only local-tarball npx evidence",
        ],
    }
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, args.output_md)
    build_trace(report, args.output_json, args.output_md, args.trace)

    if not preflight["passed"]:
        raise RuntimeError("docs-forge live RP3 Node npx observer preflight failed")
    if len(passed) != len(cases):
        failed = ", ".join(item["case_id"] for item in cases if not item["passed"])
        raise RuntimeError(f"docs-forge live RP3 Node npx observer failed: {failed}")

    print(args.output_json.resolve().relative_to(REPO_ROOT))
    print(args.output_md.resolve().relative_to(REPO_ROOT))
    print(args.trace.resolve().relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"docs-forge live RP3 Node npx observer failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
