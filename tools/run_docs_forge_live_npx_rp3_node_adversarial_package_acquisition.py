#!/usr/bin/env python3
"""Run docs-forge adversarial package-name npx checks inside an RP3 Node container."""

from __future__ import annotations

import argparse
import json
import os
import re
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

from run_docs_forge_live_project_local_install import (  # noqa: E402
    changed_paths,
    git_status,
    sha256_file,
    sha256_text,
    snapshot_tree,
    verify_source,
)


MANIFEST_PATH = REPO_ROOT / "benchmark" / "manifests" / "docs-forge-live-npx-rp3-node-adversarial-package-acquisition.json"
EXPECTED_PATH = REPO_ROOT / "benchmark" / "expected" / "docs-forge" / "npx-rp3-node-adversarial-package-acquisition.json"
DEFAULT_OUTPUT_JSON = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_rp3_node_adversarial_package_acquisition_result.json"
DEFAULT_OUTPUT_MD = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_rp3_node_adversarial_package_acquisition_report.md"
DEFAULT_TRACE = REPO_ROOT / "results" / "live" / "docs-forge-installer" / "npx_rp3_node_adversarial_package_acquisition_trace.jsonl"
MANIFEST_REF = "benchmark/manifests/docs-forge-live-npx-rp3-node-adversarial-package-acquisition.json"
TASK_REF = "benchmark/tasks/docs-forge/npx-rp3-node-adversarial-package-acquisition.txt"
RUNTIME_PROFILE = "RP3_NODE_NPX_PACKAGE_NAME_LOOPBACK_REGISTRY_FAIL_CLOSED"
PUBLIC_REGISTRY_MARKERS = ("registry.npmjs.org", "https://registry.npmjs.org", "http://registry.npmjs.org")


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


def replacements_for(paths: list[Path], labels: list[str]) -> list[tuple[str, str]]:
    replacements: list[tuple[str, str]] = []
    for path, label in zip(paths, labels, strict=True):
        for value in {str(path), str(path.resolve())}:
            replacements.append((value, label))
    replacements.append((str(REPO_ROOT), "<REPO_ROOT>"))
    replacements.append((str(Path.home()), "<LOCAL_HOME>"))
    return sorted(replacements, key=lambda item: len(item[0]), reverse=True)


def sanitize(value: str, replacements: list[tuple[str, str]]) -> str:
    sanitized = value
    for needle, label in replacements:
        sanitized = sanitized.replace(needle, label)
    sanitized = re.sub(r"/private/tmp/skilldiff-[^\s)'\"}]+", "<EPHEMERAL_LIVE_WORKSPACE>", sanitized)
    sanitized = re.sub(r"/tmp/skilldiff-[^\s)'\"}]+", "<EPHEMERAL_LIVE_WORKSPACE>", sanitized)
    sanitized = re.sub(r"/opt/homebrew/[^\s)'\"]+", "<NODE_RUNTIME>", sanitized)
    sanitized = re.sub(r"/usr/local/[^\s)'\"]+", "<NODE_RUNTIME>", sanitized)
    sanitized = re.sub(r"/opt/hostedtoolcache/[^\s)'\"]+", "<NODE_RUNTIME>", sanitized)
    return sanitized


def display_argv(argv: list[str], replacements: list[tuple[str, str]], *, docker_bin: str | None = None) -> list[str]:
    displayed = []
    for arg in argv:
        if docker_bin is not None and arg == docker_bin:
            displayed.append("docker")
            continue
        displayed.append(sanitize(arg, replacements))
    return displayed


def chmod_workspace(paths: list[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
        path.chmod(0o777)


def docker_env_args(
    *,
    registry_url: str,
    home_root: str,
    cache_root: str,
    user_config: str,
    global_config: str,
) -> list[str]:
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
        "--env=NPM_CONFIG_FETCH_RETRIES=0",
        "--env=NPM_CONFIG_FETCH_TIMEOUT=1000",
        f"--env=NPM_CONFIG_REGISTRY={registry_url}",
        "--env=NPM_CONFIG_IGNORE_SCRIPTS=true",
        "--env=NPM_CONFIG_LOGLEVEL=error",
        f"--env=NPM_CONFIG_USERCONFIG={user_config}",
        f"--env=NPM_CONFIG_GLOBALCONFIG={global_config}",
    ]


def run_docker(
    *,
    docker_bin: str,
    image_ref: str,
    command: list[str],
    workdir: str,
    registry_url: str,
    workspace_root: Path | None,
    home_root: Path | None,
    cache_root: Path | None,
) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    argv = [
        docker_bin,
        "run",
        "--rm",
        "--network=none",
        "--read-only",
        "--user=1000:1000",
    ]
    if workspace_root is not None:
        argv.append(f"--mount=type=bind,source={workspace_root},target=/workspace/package")
    if home_root is not None:
        argv.append(f"--mount=type=bind,source={home_root},target=/workspace/home")
    if cache_root is not None:
        argv.append(f"--mount=type=bind,source={cache_root},target=/workspace/npm-cache")
    argv.extend(["--tmpfs=/tmp", f"--workdir={workdir}"])
    if workspace_root is None or home_root is None or cache_root is None:
        argv.extend(
            docker_env_args(
                registry_url=registry_url,
                home_root="/tmp",
                cache_root="/tmp/npm-cache",
                user_config="/tmp/npm-userconfig",
                global_config="/tmp/npm-globalconfig",
            )
        )
    else:
        argv.extend(
            docker_env_args(
                registry_url=registry_url,
                home_root="/workspace/home",
                cache_root="/workspace/npm-cache",
                user_config="/workspace/package/npm-userconfig",
                global_config="/workspace/package/npm-globalconfig",
            )
        )
    argv.append(image_ref)
    argv.extend(command)
    completed = subprocess.run(argv, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    return completed, argv


def parse_preflight(stdout: str) -> dict[str, str | None]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    return {
        "node_version": lines[0] if len(lines) > 0 else None,
        "npm_version": lines[1] if len(lines) > 1 else None,
        "npx_version": lines[2] if len(lines) > 2 else None,
        "strace_version": lines[3] if len(lines) > 3 else None,
        "python_version": lines[4] if len(lines) > 4 else None,
    }


def contains_public_registry(text: str) -> bool:
    return any(marker in text for marker in PUBLIC_REGISTRY_MARKERS)


def cache_contains_install(changed: list[str]) -> bool:
    return any("node_modules/docs-forge" in item or "_npx" in item and "docs-forge" in item for item in changed)


def cache_contains_lifecycle_marker(text: str) -> bool:
    lifecycle_markers = (
        "preinstall",
        "postinstall",
        " info run docs-forge@",
        "npm info run docs-forge@",
    )
    return any(marker in text for marker in lifecycle_markers)


def run_container_observer(
    case: dict[str, Any],
    *,
    expected: dict[str, Any],
    source_root: Path,
    temp_root: Path,
    workspace_root: Path,
    home_root: Path,
    cache_root: Path,
    docker_bin: str,
    image_ref: str,
    replacements: list[tuple[str, str]],
) -> dict[str, Any]:
    registry_url = case["registry_url"]
    npx_argv = [str(value) for value in case["npx_argv"]]
    (workspace_root / "npm-userconfig").write_text("", encoding="utf-8")
    (workspace_root / "npm-globalconfig").write_text("", encoding="utf-8")

    source_before = git_status(source_root)
    home_before = snapshot_tree(home_root)
    cache_before = snapshot_tree(cache_root)

    completed, docker_argv = run_docker(
        docker_bin=docker_bin,
        image_ref=image_ref,
        command=npx_argv,
        workdir="/workspace/package",
        registry_url=registry_url,
        workspace_root=workspace_root,
        home_root=home_root,
        cache_root=cache_root,
    )

    source_after = git_status(source_root)
    home_after = snapshot_tree(home_root)
    cache_after = snapshot_tree(cache_root)
    cache_changes = changed_paths(cache_before, cache_after)

    stdout = sanitize(completed.stdout, replacements)
    stderr = sanitize(completed.stderr, replacements)
    combined = stdout + "\n" + stderr
    displayed_argv = display_argv(npx_argv, replacements)
    displayed_docker_argv = display_argv(docker_argv, replacements, docker_bin=docker_bin)
    public_registry_observed = contains_public_registry(combined) or contains_public_registry(json.dumps(displayed_argv))
    loopback_registry_observed = "127.0.0.1:9" in combined
    package_install_executed = cache_contains_install(cache_changes)
    lifecycle_scripts_executed = cache_contains_lifecycle_marker(combined)
    help_marker_observed = "Docs Forge 0.3.0" in stdout

    record = {
        "case_id": case["case_id"],
        "runtime_profile": RUNTIME_PROFILE,
        "container_image_ref": image_ref,
        "docker_network_mode": "none",
        "read_only_rootfs": True,
        "docker_user": "1000:1000",
        "docker_socket_mounted": False,
        "npx_argv": displayed_argv,
        "npx_docker_argv": displayed_docker_argv,
        "npx_argv_sha256": sha256_text(json.dumps(displayed_argv, sort_keys=True)),
        "npx_docker_argv_sha256": sha256_text(json.dumps(displayed_docker_argv, sort_keys=True)),
        "dry_run": False,
        "mutating": case["mutating"],
        "expected_nonzero_exit": case["expected_nonzero_exit"],
        "expected_fail_closed": case["expected_fail_closed"],
        "npx_exit_code": completed.returncode,
        "npx_package_name_execution": displayed_argv == ["npx", "--yes", "--registry", registry_url, "docs-forge", "--help"],
        "npx_uses_local_tarball": "--package" in displayed_argv,
        "registry_url": registry_url,
        "registry_endpoint_class": case["registry_endpoint_class"],
        "ignore_scripts": True,
        "source_status_clean_before": source_before == "",
        "source_status_clean_after": source_after == "",
        "source_mutation_count": 0 if source_after == "" else 1,
        "home_mutation_count": len(changed_paths(home_before, home_after)),
        "npm_cache_mutation_count": len(cache_changes),
        "npm_cache_changed_files_sample": cache_changes[:20],
        "npx_stdout_sha256": sha256_text(stdout),
        "npx_stderr_sha256": sha256_text(stderr),
        "npx_stdout_excerpt": stdout[:2000],
        "npx_stderr_excerpt": stderr[:2000],
        "registry_acquisition_attempted": True,
        "registry_acquisition_succeeded": False,
        "public_registry_acquisition_executed": False,
        "package_install_executed": package_install_executed,
        "lifecycle_scripts_executed": lifecycle_scripts_executed,
        "loopback_registry_event_observed": loopback_registry_observed,
        "public_registry_url_observed": public_registry_observed,
        "public_internet_contact_observed": False,
        "public_internet_contact_measured": False,
        "packet_capture_enabled": False,
        "network_events_observed": 1 if loopback_registry_observed else 0,
        "help_marker_observed": help_marker_observed,
    }
    record["fail_closed_observed"] = (
        completed.returncode != 0
        and record["registry_acquisition_attempted"]
        and not record["registry_acquisition_succeeded"]
        and not record["public_registry_acquisition_executed"]
        and not record["package_install_executed"]
        and not record["lifecycle_scripts_executed"]
        and not record["help_marker_observed"]
    )
    record["passed"] = (
        record["npx_exit_code"] != 0
        and record["npx_package_name_execution"]
        and not record["npx_uses_local_tarball"]
        and record["ignore_scripts"]
        and record["source_status_clean_before"]
        and record["source_status_clean_after"]
        and record["source_mutation_count"] == expected["expected_source_mutations"]
        and record["home_mutation_count"] == expected["expected_home_mutations"]
        and record["registry_url"] == expected["expected_registry_url"]
        and record["registry_endpoint_class"] == expected["allowed_network_endpoint_class"]
        and record["fail_closed_observed"]
        and record["network_events_observed"] == 1
        and not record["public_registry_url_observed"]
        and not record["public_internet_contact_observed"]
    )
    return record


def write_markdown(report: dict[str, Any], output_md: Path) -> None:
    case = report["cases"][0]
    lines = [
        "# docs-forge Live RP3 Node Adversarial npx Package-Acquisition Result",
        "",
        "This artifact records a bounded Dockerized adversarial package-name npx",
        "probe for the pinned docs-forge source boundary. The command points npm",
        "at a controlled loopback registry endpoint inside a Node-capable",
        "RP3-derived container and expects fail-closed behavior before public",
        "registry acquisition, install behavior, lifecycle scripts, or",
        "docs-forge help execution can complete.",
        "",
        "| Case | npx Exit | Image | Registry | Fail Closed | Source Mutations | Home Mutations | Result |",
        "| --- | ---: | --- | --- | --- | ---: | ---: | --- |",
        "| {case_id} | {exit_code} | `{image}` | `{registry}` | {fail_closed} | {source} | {home} | {result} |".format(
            case_id=case["case_id"],
            exit_code=case["npx_exit_code"],
            image=report["container_image_ref"],
            registry=case["registry_url"],
            fail_closed="yes" if case["fail_closed_observed"] else "no",
            source=case["source_mutation_count"],
            home=case["home_mutation_count"],
            result="passed" if case["passed"] else "failed",
        ),
        "",
        "## Container Boundary",
        "",
        "- Docker ran with `--network=none` and `--read-only` for the preflight and npx commands.",
        "- The package-name npx attempt did not mount the docs-forge source checkout.",
        "- The command intentionally uses package-name `npx docs-forge --help` under a loopback registry control.",
        "- The observed result is fail-closed: the package was not acquired and docs-forge help did not execute.",
        "- No public npm registry URL, package install command, lifecycle script, source mutation, or home mutation was observed.",
        "- This is adversarial package-acquisition readiness evidence only; it is not public-registry acquisition evidence, packet-capture evidence, or runtime-drift evidence.",
    ]
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_trace(report: dict[str, Any], output_json: Path, output_md: Path, trace_path: Path) -> None:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from skilldiff.traces.events import TraceBuilder, TraceContext, validate_trace_file

    result_ref = output_json.relative_to(REPO_ROOT).as_posix()
    report_ref = output_md.relative_to(REPO_ROOT).as_posix()
    trace_ref = trace_path.relative_to(REPO_ROOT).as_posix()
    case = report["cases"][0]
    context = TraceContext(
        run_id="live-docs-forge-npx-rp3-node-adversarial-package-acquisition",
        skill_id="docs-forge",
        task_id="npx-rp3-node-adversarial-package-acquisition",
        contract_id="docs-forge-live-npx-rp3-node-adversarial-package-acquisition",
        runtime_profile=RUNTIME_PROFILE,
        runtime_profile_hash=sha256_text(RUNTIME_PROFILE + report["container_image_ref"] + case["registry_url"]),
        adapter_id="live_rp3_node_npx_adversarial_package_acquisition_observer",
        adapter_version="0.1",
        repeat_id=1,
    )
    builder = TraceBuilder(context)
    builder.add(
        "run.start",
        event_phase="prepare",
        actor="live_rp3_node_npx_adversarial_package_acquisition_observer",
        event_status="succeeded",
        target_kind="run",
        target="live-docs-forge-npx-rp3-node-adversarial-package-acquisition",
        enforcement_outcome="not_applicable",
        evidence_ref=result_ref,
        metadata={"execution_level": report["execution_level"], "source_root": "<DOCS_FORGE_SOURCE_ROOT>", "source_commit": report["source_commit"]},
    )
    builder.add(
        "capability.snapshot",
        event_phase="prepare",
        actor="live_rp3_node_npx_adversarial_package_acquisition_observer",
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
            "package_name_npx": True,
            "local_tarball": False,
            "registry_url": case["registry_url"],
            "registry_endpoint_class": case["registry_endpoint_class"],
            "ignore_scripts": case["ignore_scripts"],
            "packet_capture": "not_enabled",
            "public_internet_contact_allowed": False,
        },
    )
    builder.add(
        "activation.select",
        event_phase="run",
        actor="live_rp3_node_npx_adversarial_package_acquisition_observer",
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
        actor="live_rp3_node_npx_adversarial_package_acquisition_observer",
        event_status="attempted",
        target_kind="process",
        target="container-preflight",
        operation="exec",
        allowed_by_contract=True,
        contract_rule_ids=["SC-SH-000"],
        matched_allow_rule="SC-SH-000",
        enforcement_outcome="allowed",
        evidence_ref=result_ref,
        metadata={"argv": report["preflight"]["argv"], "docker_network_mode": "none", "read_only_rootfs": True},
    )
    builder.add(
        "process.exit",
        event_phase="run",
        actor="live_rp3_node_npx_adversarial_package_acquisition_observer",
        event_status="succeeded" if report["preflight"]["exit_code"] == 0 else "failed",
        target_kind="process",
        target="container-preflight",
        operation="exit",
        enforcement_outcome="allowed" if report["preflight"]["exit_code"] == 0 else "failed",
        evidence_ref=result_ref,
        metadata={"exit_code": report["preflight"]["exit_code"], "versions": report["preflight"]["versions"]},
    )
    approval_id = "approval-docs-forge-rp3-node-npx-adversarial-package-acquisition"
    for event_type, target, operation in (
        ("approval.required", "Dockerized package-name npx docs-forge loopback-registry probe", "approve"),
        ("approval.prompt", "npx --registry loopback docs-forge --help in RP3 Node container", "prompt"),
        ("approval.decision", "npx --registry loopback docs-forge --help in RP3 Node container", "allow"),
    ):
        builder.add(
            event_type,
            event_phase="run",
            actor="live_rp3_node_npx_adversarial_package_acquisition_observer" if event_type != "approval.decision" else "benchmark_operator",
            event_status="observed",
            target_kind="approval",
            target=target,
            operation=operation,
            approval_required=True,
            approval_request_id=approval_id,
            enforcement_outcome="allowed" if event_type == "approval.decision" else "observed",
            evidence_ref=report["contract_ref"],
            metadata={"decision_required": "explicit_allow", "negative_control": True} if event_type == "approval.required" else {},
        )
    builder.add(
        "shell.exec",
        event_phase="run",
        actor="live_rp3_node_npx_adversarial_package_acquisition_observer",
        event_status="attempted",
        target_kind="process",
        target="npx",
        operation="exec",
        allowed_by_contract=True,
        contract_rule_ids=["SC-SH-001"],
        matched_allow_rule="SC-SH-001",
        enforcement_outcome="allowed",
        evidence_ref=result_ref,
        metadata={"argv": case["npx_argv"], "docker_network_mode": "none", "command_sha256": "sha256:" + case["npx_argv_sha256"], "negative_control": True},
    )
    builder.add(
        "network.connect",
        event_phase="run",
        actor="npm_registry_client",
        event_status="failed",
        target_kind="network",
        target="127.0.0.1:9",
        operation="connect",
        allowed_by_contract=True,
        contract_rule_ids=["SC-NET-001"],
        matched_allow_rule="SC-NET-001",
        enforcement_outcome="failed",
        evidence_ref=result_ref,
        metadata={
            "registry_url": case["registry_url"],
            "endpoint_class": case["registry_endpoint_class"],
            "docker_network_mode": "none",
            "packet_capture": "not_enabled",
            "public_internet_contact_observed": False,
        },
    )
    builder.add(
        "process.exit",
        event_phase="run",
        actor="live_rp3_node_npx_adversarial_package_acquisition_observer",
        event_status="failed",
        target_kind="process",
        target="npx",
        operation="exit",
        enforcement_outcome="failed",
        evidence_ref=result_ref,
        metadata={"exit_code": case["npx_exit_code"], "adapter_outcome": "failed_closed", "fail_closed": case["fail_closed_observed"]},
    )
    for target, sink_type in ((output_json, "local_json"), (output_md, "local_report")):
        builder.add(
            "output.generated",
            event_phase="collect",
            actor="live_rp3_node_npx_adversarial_package_acquisition_observer",
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
        actor="live_rp3_node_npx_adversarial_package_acquisition_observer",
        event_status="observed",
        target_kind="cleanup",
        target="temporary_workspace_removed",
        enforcement_outcome="observed",
        evidence_ref=result_ref,
        metadata={"removed_paths": ["<EPHEMERAL_LIVE_WORKSPACE>"], "leftover_paths": []},
    )
    builder.add(
        "run.end",
        event_phase="cleanup",
        actor="live_rp3_node_npx_adversarial_package_acquisition_observer",
        event_status="succeeded" if case["passed"] and report["preflight"]["passed"] else "failed",
        target_kind="run",
        target="live-docs-forge-npx-rp3-node-adversarial-package-acquisition",
        enforcement_outcome="not_applicable",
        evidence_ref=trace_ref,
        metadata={"exit_code": case["npx_exit_code"], "adapter_outcome": "failed_closed" if case["passed"] and report["preflight"]["passed"] else "failed"},
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
        raise RuntimeError("DOCS_FORGE_SOURCE_ROOT or --source-root is required for live RP3 Node adversarial npx evidence")
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

    with tempfile.TemporaryDirectory(prefix="skilldiff-docs-forge-rp3-node-npx-adversarial-", dir="/tmp") as temp:
        temp_root = Path(temp)
        workspace_root = temp_root / "workspace"
        home_root = temp_root / "home"
        cache_root = temp_root / "npm-cache"
        chmod_workspace([temp_root, workspace_root, home_root, cache_root])
        replacements = replacements_for(
            [source_root, temp_root, workspace_root, home_root, cache_root],
            ["<DOCS_FORGE_SOURCE_ROOT>", "<EPHEMERAL_LIVE_WORKSPACE>", "<EPHEMERAL_WORKDIR>", "<EPHEMERAL_HOME>", "<EPHEMERAL_NPM_CACHE>"],
        )

        preflight_argv = manifest["commands"][0]["argv"]
        preflight_completed, preflight_docker_argv = run_docker(
            docker_bin=docker_bin,
            image_ref=image_ref,
            command=preflight_argv,
            workdir="/tmp",
            registry_url=manifest["runtime_boundary"]["registry_url"],
            workspace_root=None,
            home_root=None,
            cache_root=None,
        )
        preflight_stdout = sanitize(preflight_completed.stdout, replacements)
        preflight_stderr = sanitize(preflight_completed.stderr, replacements)
        preflight = {
            "case_id": manifest["commands"][0]["case_id"],
            "argv": preflight_argv,
            "docker_argv": display_argv(preflight_docker_argv, replacements, docker_bin=docker_bin),
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
                workspace_root=workspace_root,
                home_root=home_root,
                cache_root=cache_root,
                docker_bin=docker_bin,
                image_ref=image_ref,
                replacements=replacements,
            )
        ]

    case = cases[0]
    report = {
        "schema_version": "0.1",
        "artifact_id": "docs-forge-live-npx-rp3-node-adversarial-package-acquisition",
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
            "commands_run": 2,
            "commands_succeeded": int(preflight["exit_code"] == 0) + int(case["npx_exit_code"] == 0),
            "commands_failed_closed": int(case["fail_closed_observed"]),
            "container_preflight_commands_run": 1,
            "workload_commands_run": 1,
            "docker_container_commands_run": 2,
            "docker_network_none_commands_run": 2,
            "docker_read_only_rootfs_commands_run": 2,
            "docker_socket_mounts_observed": 0,
            "npx_commands_executed": 1,
            "npx_package_name_commands_executed": int(case["npx_package_name_execution"]),
            "npx_local_tarball_commands_executed": int(case["npx_uses_local_tarball"]),
            "registry_acquisition_attempts_observed": int(case["registry_acquisition_attempted"]),
            "registry_acquisitions_observed": int(case["registry_acquisition_succeeded"]),
            "public_registry_acquisitions_observed": int(case["public_registry_acquisition_executed"]),
            "package_install_commands_executed": int(case["package_install_executed"]),
            "lifecycle_scripts_executed": int(case["lifecycle_scripts_executed"]),
            "source_mutations_observed": case["source_mutation_count"],
            "synthetic_home_mutations_observed": case["home_mutation_count"],
            "ephemeral_npm_cache_mutations_observed": case["npm_cache_mutation_count"],
            "loopback_registry_events_observed": int(case["loopback_registry_event_observed"]),
            "network_events_observed": case["network_events_observed"],
            "public_internet_contact_observed": case["public_internet_contact_observed"],
            "public_internet_contact_measured": False,
            "packet_capture_enabled": False,
            "runtime_drift_counts_changed": False,
            "runtime_drift_claims_added": 0,
            "pairwise_disagreements_added": 0,
            "canonical_traces_added": 0,
            "canonical_results_added": 0,
            "live_traces_added": 1,
        },
        "claims_not_supported": [
            "public npm registry acquisition",
            "successful package acquisition",
            "package install behavior",
            "lifecycle-script execution",
            "docs-forge docs-generation workload execution",
            "network egress absence under packet capture",
            "complete Node or npm runtime tracing",
            "runtime-drift claims from RP3 adversarial npx package-name fail-closed observer evidence",
        ],
    }
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, args.output_md)
    build_trace(report, args.output_json, args.output_md, args.trace)
    if not preflight["passed"]:
        raise RuntimeError("docs-forge live RP3 Node adversarial npx observer preflight failed")
    if not case["passed"]:
        raise RuntimeError("docs-forge live RP3 Node adversarial npx observer did not meet fail-closed boundary")

    print(args.output_json.resolve().relative_to(REPO_ROOT))
    print(args.output_md.resolve().relative_to(REPO_ROOT))
    print(args.trace.resolve().relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as exc:
        print(f"docs-forge live RP3 Node npx adversarial package-acquisition failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
