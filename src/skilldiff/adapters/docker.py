"""Docker adapter for the RP3 MVP profile."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import textwrap

from .local import _PYTHON_READ_PROVENANCE_SHIM as _CONTROLLED_PYTHON_PROVENANCE_SHIM
from .base import (
    CleanupResult,
    CollectedRun,
    PreparedRun,
    RunExecution,
    RunSpec,
    RuntimeAdapter,
    append_jsonl,
    base_capability_snapshot,
    canonical_profile_hash,
    ensure_artifact_files,
    stable_run_id,
    utc_now,
    write_json,
    write_jsonl,
)
from skilldiff.traces.events import (
    diff_snapshots,
    extract_canary_labels,
    scan_text_for_canaries,
    snapshot_tree,
)


class DockerDryRunAdapter(RuntimeAdapter):
    adapter_id = "docker_adapter"

    def capability_snapshot(self, runtime_profile: dict[str, Any]) -> dict[str, Any]:
        snapshot = base_capability_snapshot(runtime_profile, self.adapter_id)
        snapshot["container_constraints"] = runtime_profile["adapter"]["runtime_constraints"]
        return snapshot

    def prepare(
        self,
        run_spec: RunSpec,
        runtime_profile: dict[str, Any],
        workspace_seed: Path,
        contract: dict[str, Any],
        task_prompt: str,
    ) -> PreparedRun:
        if runtime_profile["adapter"]["adapter_id"] != self.adapter_id:
            raise ValueError(f"profile requires {runtime_profile['adapter']['adapter_id']}, not {self.adapter_id}")

        constraints = _validated_constraints(runtime_profile)
        run_id = stable_run_id(self.adapter_id, runtime_profile, run_spec)
        run_dir = (run_spec.output_root / run_id).resolve()
        if run_dir.exists():
            shutil.rmtree(run_dir)
        workspace_root = run_dir / "workspace"
        seed_copy_path = workspace_root / "repo"
        output_workspace_path = workspace_root / "out"
        copied_files = _copy_seed_workspace(workspace_seed, seed_copy_path, _repo_exclude_globs(runtime_profile))
        output_workspace_path.mkdir(parents=True, exist_ok=True)
        (workspace_root / "tmp").mkdir(parents=True, exist_ok=True)
        files = ensure_artifact_files(run_dir)
        command = run_spec.command or []
        mounts = _resolved_mounts(constraints, seed_copy_path, output_workspace_path)
        read_provenance = _read_provenance_config(command, runtime_profile, output_workspace_path)
        execution_plan = _build_execution_plan(
            command,
            runtime_profile,
            contract,
            output_workspace_path,
            task_prompt,
            constraints,
            mounts,
            run_spec.dry_run,
            run_dir,
            read_provenance,
        )
        invocation = execution_plan["container_invocation"]

        write_json(files["capabilities"], self.capability_snapshot(runtime_profile))
        write_json(
            files["run_metadata"],
            {
                "adapter_id": self.adapter_id,
                "adapter_version": runtime_profile["adapter"]["adapter_version"],
                "contract_id": run_spec.contract_id,
                "command": command,
                "dry_run": run_spec.dry_run,
                "prepared_at": utc_now(),
                "profile_id": runtime_profile["profile_id"],
                "profile_hash": canonical_profile_hash(runtime_profile),
                "repeat_id": run_spec.repeat_id,
                "run_id": run_id,
                "skill_id": run_spec.skill_id,
                "task_id": run_spec.task_id,
                "workspace_copied_file_count": copied_files,
                "workspace_mode": "copied_seed_read_only_repo_plus_writable_output",
                "workspace_seed": str(workspace_seed),
                "workspace_seed_copy": str(seed_copy_path),
                "container_invocation": invocation,
            },
        )
        write_json(files["execution_plan"], execution_plan)
        write_json(files["env_manifest"], execution_plan["env_manifest"])
        write_json(files["mount_manifest"], {"mounts": mounts, "tmpfs": execution_plan["tmpfs_mounts"]})
        write_json(files["instrumentation_status"], _initial_instrumentation_status(self.adapter_id, read_provenance))
        write_jsonl(files["approvals"], [])
        write_jsonl(files["approval_events"], [])
        write_jsonl(files["network_attempts"], [])
        write_jsonl(files["network_events"], [])
        write_jsonl(files["network_sink_requests"], [])
        write_jsonl(files["process_events"], [])
        write_jsonl(files["file_read_events"], [])
        write_jsonl(files["file_write_events"], [])
        write_jsonl(files["canary_hits"], [])
        write_jsonl(
            files["file_observations"],
            [
                {
                    "copied_file_count": copied_files,
                    "event": "workspace_seed_copied",
                    "path": str(workspace_seed),
                    "profile_id": runtime_profile["profile_id"],
                    "seed_copy_path": str(seed_copy_path),
                    "timestamp": utc_now(),
                },
                {
                    "event": "mount_plan_registered",
                    "mount_mode": "read_only_seed_plus_writable_artifacts",
                    "profile_id": runtime_profile["profile_id"],
                    "timestamp": utc_now(),
                },
            ],
        )
        write_jsonl(
            files["adapter_events"],
            [
                {
                    "adapter_id": self.adapter_id,
                    "event": "prepare",
                    "mode": "dry_run" if run_spec.dry_run else "live",
                    "timestamp": utc_now(),
                }
            ],
        )

        return PreparedRun(
            run_id=run_id,
            profile_id=runtime_profile["profile_id"],
            runtime_profile_hash=canonical_profile_hash(runtime_profile),
            adapter_id=self.adapter_id,
            adapter_version=runtime_profile["adapter"]["adapter_version"],
            workspace_path=output_workspace_path,
            artifacts_dir=run_dir,
            run_metadata_path=files["run_metadata"],
            capabilities_path=files["capabilities"],
            approval_plan_path=files["approvals"],
            invocation=invocation,
            dry_run=run_spec.dry_run,
        )

    def run(self, prepared_run: PreparedRun) -> RunExecution:
        if not prepared_run.dry_run:
            return _run_docker_live(self.adapter_id, prepared_run)

        files = ensure_artifact_files(prepared_run.artifacts_dir)
        plan = json.loads(files["execution_plan"].read_text(encoding="utf-8"))
        command = plan["command"]["argv"]
        started_at = utc_now()
        files["stdout"].write_text("docker adapter dry run\n", encoding="utf-8")
        files["stderr"].write_text("", encoding="utf-8")
        append_jsonl(
            files["process_events"],
            {
                "argv": command,
                "container_invocation": prepared_run.invocation,
                "event": "shell.exec",
                "operation": "exec",
                "status": "not_executed",
                "target": command[0] if command else None,
                "timestamp": started_at,
            },
        )
        append_jsonl(
            files["adapter_events"],
            {
                "adapter_id": self.adapter_id,
                "event": "run",
                "mode": "dry_run",
                "outcome": "not_executed",
                "timestamp": started_at,
            },
        )
        ended_at = utc_now()
        return RunExecution(
            adapter_outcome="dry_run_not_executed",
            started_at=started_at,
            ended_at=ended_at,
            exit_code=0,
            stdout_path=files["stdout"],
            stderr_path=files["stderr"],
            adapter_events_path=files["adapter_events"],
            container_id=None,
        )

    def collect(self, prepared_run: PreparedRun, run_execution: RunExecution) -> CollectedRun:
        files = ensure_artifact_files(prepared_run.artifacts_dir)
        generated_outputs = _generated_outputs(prepared_run.workspace_path)
        canary_observations = _read_jsonl(files["canary_hits"])
        write_json(
            files["outputs_manifest"],
            {
                "adapter_outcome": run_execution.adapter_outcome,
                "container_id": run_execution.container_id,
                "generated_outputs": generated_outputs,
                "mode": "dry_run" if prepared_run.dry_run else "live",
                "run_id": prepared_run.run_id,
            },
        )
        append_jsonl(
            files["adapter_events"],
            {
                "adapter_id": self.adapter_id,
                "event": "collect",
                "timestamp": utc_now(),
            },
        )
        return CollectedRun(
            capabilities_path=files["capabilities"],
            outputs_manifest_path=files["outputs_manifest"],
            raw_trace_sources=[
                files["adapter_events"],
                files["approvals"],
                files["network_attempts"],
                files["network_events"],
                files["network_sink_requests"],
                files["file_observations"],
                files["process_events"],
                files["file_read_events"],
                files["file_write_events"],
                files["canary_hits"],
            ],
            canary_observations=canary_observations,
            approval_transcript_path=files["approvals"],
        )

    def cleanup(self, prepared_run: PreparedRun, run_execution: RunExecution) -> CleanupResult:
        files = ensure_artifact_files(prepared_run.artifacts_dir)
        if prepared_run.dry_run:
            status = "recorded_no_live_container"
        elif run_execution.container_id:
            status = "recorded_container_removed_by_docker_rm"
        else:
            status = "recorded_no_container_to_remove"
        result = CleanupResult(
            status=status,
            removed_paths=[],
            leftover_paths=[prepared_run.artifacts_dir],
            cleanup_path=files["cleanup"],
        )
        write_json(
            files["cleanup"],
            {
                "container_id": run_execution.container_id,
                "leftover_paths": [str(path) for path in result.leftover_paths],
                "removed_paths": [],
                "run_id": prepared_run.run_id,
                "status": result.status,
                "timestamp": utc_now(),
            },
        )
        return result


def _validated_constraints(runtime_profile: dict[str, Any]) -> dict[str, Any]:
    constraints = runtime_profile["adapter"].get("runtime_constraints")
    if not constraints:
        raise ValueError("docker_adapter requires adapter.runtime_constraints in the runtime profile")
    if constraints.get("type") != "docker_container":
        raise ValueError("docker_adapter only supports docker_container runtime constraints")
    if constraints.get("docker_socket_mounted"):
        raise ValueError("docker socket mounts are outside the RP3 benchmark boundary")
    if not constraints.get("container_image_ref"):
        raise ValueError("docker_adapter requires adapter.runtime_constraints.container_image_ref")
    return constraints


def _repo_exclude_globs(runtime_profile: dict[str, Any]) -> list[str]:
    excludes = []
    for root in runtime_profile["features"]["filesystem"].get("roots", []):
        if root.get("id") != "repo":
            continue
        for pattern in root.get("exclude_globs", []):
            if not isinstance(pattern, str):
                continue
            if pattern.startswith("./repo/"):
                pattern = "./" + pattern.removeprefix("./repo/")
            elif pattern.startswith("repo/"):
                pattern = "./" + pattern.removeprefix("repo/")
            elif not pattern.startswith("./"):
                pattern = "./" + pattern
            excludes.append(pattern)
    return excludes


def _copy_seed_workspace(workspace_seed: Path, destination: Path, exclude_globs: list[str]) -> int:
    if not workspace_seed.exists():
        raise FileNotFoundError(f"workspace seed does not exist: {workspace_seed}")
    if workspace_seed.is_symlink():
        raise ValueError(f"workspace seed path is a symlink, which RP3 rejects: {workspace_seed}")
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    if workspace_seed.is_file():
        destination.mkdir(parents=True, exist_ok=True)
        rel = "./" + workspace_seed.name
        if _excluded_path(rel, exclude_globs):
            return 0
        shutil.copy2(workspace_seed, destination / workspace_seed.name)
        return 1

    copied = 0
    for path in workspace_seed.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"workspace seed contains symlink, which RP3 rejects: {path}")
        rel = "./" + path.relative_to(workspace_seed).as_posix()
        if _excluded_path(rel, exclude_globs):
            continue
        target = destination / path.relative_to(workspace_seed)
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            copied += 1
    return copied


def _excluded_path(path: str, exclude_globs: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in exclude_globs)


def _resolved_mounts(
    constraints: dict[str, Any],
    seed_copy_path: Path,
    output_workspace_path: Path,
) -> list[dict[str, Any]]:
    mounts: list[dict[str, Any]] = []
    for mount in constraints.get("mounts", []):
        source = mount.get("source")
        if source == "<seed>":
            resolved_source = seed_copy_path
        elif source == "<artifacts>":
            resolved_source = output_workspace_path
        else:
            resolved_source = Path(str(source)).expanduser()
        mounts.append(
            {
                "source": str(resolved_source),
                "target": mount["target"],
                "mode": mount["mode"],
            }
        )
    return mounts


def _build_execution_plan(
    command: list[str],
    runtime_profile: dict[str, Any],
    contract: dict[str, Any],
    workspace_path: Path,
    task_prompt: str,
    constraints: dict[str, Any],
    mounts: list[dict[str, Any]],
    dry_run: bool,
    run_dir: Path,
    read_provenance: dict[str, Any],
) -> dict[str, Any]:
    profile_allowed, profile_reasons = _profile_command_decision(command, runtime_profile)
    contract_allowed, contract_reasons, rule_ids = _contract_command_decision(command, contract)
    image_allowed, image_reasons = _image_decision(runtime_profile, constraints)
    execution_allowed = bool(command) and profile_allowed and contract_allowed and image_allowed and not dry_run
    reasons = profile_reasons + contract_reasons + image_reasons
    if dry_run:
        reasons.append("dry run requested")
    timeout_seconds = runtime_profile["features"]["shell"]["timeout_seconds"]
    env_allowlist = runtime_profile["features"]["credentials"].get("env_allowlist", [])
    synthetic_env = _synthetic_env(runtime_profile)
    if read_provenance.get("python_shim_enabled"):
        synthetic_env.update(
            {
                "PYTHONPATH": _prepend_path_env(
                    read_provenance["container_shim_dir"],
                    synthetic_env.get("PYTHONPATH", ""),
                    separator=":",
                ),
                "SKILLDIFF_FILE_WRITE_EVENTS": read_provenance["container_write_event_path"],
            }
        )
    if read_provenance.get("python_enabled"):
        synthetic_env.update(
            {
                "SKILLDIFF_FILE_READ_EVENTS": read_provenance["container_event_path"],
                "SKILLDIFF_READ_PROVENANCE_MODEL": read_provenance["instrumentation_model"],
            }
        )
    if read_provenance.get("network_enabled"):
        fake_sink_url = _fake_sink_url(read_provenance)
        synthetic_env.update(
            {
                "SKILLDIFF_NETWORK_EVENTS": read_provenance["container_network_event_path"],
                "SKILLDIFF_NETWORK_SINK_REQUESTS": read_provenance["container_network_sink_requests_path"],
                "SKILLDIFF_NETWORK_PROVENANCE_MODEL": "python_network_shim_mvp",
                "SKILLDIFF_NETWORK_MODE": read_provenance["network_mode"],
                "SKILLDIFF_FAKE_NETWORK_SINK_DOMAINS": ",".join(read_provenance["fake_sink_domains"]),
                "SKILLDIFF_CANARY_LABELS": ",".join(extract_canary_labels(contract)),
            }
        )
        if fake_sink_url:
            synthetic_env["SKILLDIFF_FAKE_SINK_URL"] = fake_sink_url
    container_workdir = _container_workdir(runtime_profile, mounts)
    tmpfs_mounts = _tmpfs_mounts(runtime_profile)
    container_command = _instrumented_container_command(command, read_provenance)
    container_invocation = _container_invocation(
        constraints,
        mounts,
        synthetic_env,
        tmpfs_mounts,
        container_workdir,
        run_dir / "container.id",
        container_command,
    )
    return {
        "schema_version": "0.1",
        "command": {
            "argv": command,
            "executable": command[0] if command else None,
            "sha256": _hash_json(command),
        },
        "execution_allowed": execution_allowed,
        "decision_reasons": reasons,
        "matched_rule_ids": rule_ids,
        "workspace_path": str(workspace_path),
        "task_prompt_hash": _hash_text(task_prompt),
        "timeout_seconds": timeout_seconds,
        "env_manifest": {
            "env_allowlist": env_allowlist,
            "host_env_forwarded": [],
            "home_is_run_workspace": False,
            "synthetic_env": sorted(synthetic_env),
        },
        "canary_labels": extract_canary_labels(contract),
        "approval_policy": runtime_profile["features"]["approvals"],
        "monitors": runtime_profile["features"]["instrumentation"],
        "container_constraints": constraints,
        "container_invocation": container_invocation,
        "container_image_ref": constraints["container_image_ref"],
        "container_command": container_command,
        "container_workdir": container_workdir,
        "mounts": mounts,
        "tmpfs_mounts": tmpfs_mounts,
        "read_provenance": read_provenance,
    }


def _container_invocation(
    constraints: dict[str, Any],
    mounts: list[dict[str, Any]],
    synthetic_env: dict[str, str],
    tmpfs_mounts: list[str],
    container_workdir: str,
    cidfile: Path,
    command: list[str],
) -> list[str]:
    invocation = [
        "docker",
        "run",
        "--rm",
        "--cidfile",
        str(cidfile),
        f"--network={constraints['network_mode']}",
        f"--user={constraints['user']}",
    ]
    if constraints.get("read_only_rootfs"):
        invocation.append("--read-only")
    for mount in mounts:
        readonly = ",readonly" if mount["mode"] == "read_only" else ""
        invocation.append(
            f"--mount=type=bind,source={mount['source']},target={mount['target']}{readonly}"
        )
    for target in tmpfs_mounts:
        invocation.append(f"--tmpfs={target}")
    for name, value in sorted(synthetic_env.items()):
        invocation.append(f"--env={name}={value}")
    invocation.append(f"--workdir={container_workdir}")
    invocation.append(constraints["container_image_ref"])
    invocation.extend(command)
    return invocation


def _run_docker_live(adapter_id: str, prepared_run: PreparedRun) -> RunExecution:
    files = ensure_artifact_files(prepared_run.artifacts_dir)
    plan = json.loads(files["execution_plan"].read_text(encoding="utf-8"))
    started_at = utc_now()
    command = plan["command"]["argv"]
    target = command[0] if command else None

    if not plan["execution_allowed"]:
        return _blocked_execution(adapter_id, prepared_run, plan, started_at)

    docker_path = _docker_executable()
    if not docker_path:
        return _docker_preflight_failed(
            adapter_id,
            prepared_run,
            plan,
            started_at,
            "docker_unavailable",
            "docker executable not found on PATH or standard local install paths\n",
        )

    inspect = subprocess.run(
        [docker_path, "image", "inspect", plan["container_image_ref"]],
        text=True,
        capture_output=True,
        check=False,
    )
    if inspect.returncode != 0:
        stderr = inspect.stderr or inspect.stdout or "docker image inspect failed\n"
        outcome = "docker_unavailable" if _docker_connection_failed(stderr) else "docker_image_unavailable"
        return _docker_preflight_failed(
            adapter_id,
            prepared_run,
            plan,
            started_at,
            outcome,
            stderr,
        )

    before = snapshot_tree(prepared_run.workspace_path)
    append_jsonl(
        files["process_events"],
        {
            "argv": command,
            "container_invocation": plan["container_invocation"],
            "cwd": plan["container_workdir"],
            "event": "shell.exec",
            "operation": "exec",
            "status": "attempted",
            "target": target,
            "timestamp": started_at,
            "command_sha256": plan["command"]["sha256"],
            "matched_rule_ids": plan["matched_rule_ids"],
        },
    )

    exit_code = 0
    outcome = "completed"
    try:
        completed = subprocess.run(
            _container_invocation_with_docker_path(plan["container_invocation"], docker_path),
            text=True,
            capture_output=True,
            timeout=plan["timeout_seconds"],
            check=False,
        )
        exit_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
        if exit_code != 0:
            outcome = "failed"
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        outcome = "timeout"
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        stderr += "\ncontainer process timed out\n"

    files["stdout"].write_text(stdout, encoding="utf-8")
    files["stderr"].write_text(stderr, encoding="utf-8")
    _merge_syscall_read_provenance_events(files, plan)
    _merge_python_read_provenance_events(files, plan)
    _merge_python_write_provenance_events(files, plan)
    _merge_python_network_events(files, plan)
    _merge_python_network_sink_requests(files, plan)
    _record_workspace_diff(files, prepared_run.workspace_path, before, plan["canary_labels"])
    _record_log_canaries(files, stdout, stderr, plan["canary_labels"])

    ended_at = utc_now()
    container_id = _read_container_id(prepared_run.artifacts_dir / "container.id")
    append_jsonl(
        files["process_events"],
        {
            "argv": command,
            "container_id": container_id,
            "event": "process.exit",
            "exit_code": exit_code,
            "operation": "exit",
            "status": "succeeded" if exit_code == 0 else "failed",
            "target": target,
            "timestamp": ended_at,
        },
    )
    append_jsonl(
        files["adapter_events"],
        {
            "adapter_id": adapter_id,
            "container_id": container_id,
            "event": "run",
            "exit_code": exit_code,
            "mode": "live",
            "outcome": outcome,
            "timestamp": ended_at,
        },
    )
    return RunExecution(
        adapter_outcome=outcome,
        started_at=started_at,
        ended_at=ended_at,
        exit_code=exit_code,
        stdout_path=files["stdout"],
        stderr_path=files["stderr"],
        adapter_events_path=files["adapter_events"],
        container_id=container_id,
    )


def _blocked_execution(
    adapter_id: str,
    prepared_run: PreparedRun,
    plan: dict[str, Any],
    started_at: str,
) -> RunExecution:
    files = ensure_artifact_files(prepared_run.artifacts_dir)
    command = plan["command"]["argv"]
    files["stdout"].write_text("", encoding="utf-8")
    files["stderr"].write_text("blocked by execution plan\n", encoding="utf-8")
    append_jsonl(
        files["process_events"],
        {
            "argv": command,
            "container_invocation": plan["container_invocation"],
            "event": "shell.exec",
            "operation": "exec",
            "status": "blocked",
            "target": command[0] if command else None,
            "timestamp": started_at,
            "decision_reasons": plan["decision_reasons"],
            "matched_rule_ids": plan["matched_rule_ids"],
        },
    )
    ended_at = utc_now()
    append_jsonl(
        files["adapter_events"],
        {
            "adapter_id": adapter_id,
            "event": "run",
            "mode": "live",
            "outcome": "blocked_by_execution_plan",
            "timestamp": ended_at,
        },
    )
    return RunExecution(
        adapter_outcome="blocked_by_execution_plan",
        started_at=started_at,
        ended_at=ended_at,
        exit_code=126,
        stdout_path=files["stdout"],
        stderr_path=files["stderr"],
        adapter_events_path=files["adapter_events"],
    )


def _docker_preflight_failed(
    adapter_id: str,
    prepared_run: PreparedRun,
    plan: dict[str, Any],
    started_at: str,
    outcome: str,
    stderr: str,
) -> RunExecution:
    files = ensure_artifact_files(prepared_run.artifacts_dir)
    command = plan["command"]["argv"]
    _mark_file_read_provenance_unavailable(files, plan, outcome)
    files["stdout"].write_text("", encoding="utf-8")
    files["stderr"].write_text(stderr, encoding="utf-8")
    append_jsonl(
        files["process_events"],
        {
            "argv": command,
            "container_invocation": plan["container_invocation"],
            "event": "shell.exec",
            "operation": "exec",
            "status": "failed",
            "target": command[0] if command else None,
            "timestamp": started_at,
            "decision_reasons": [outcome],
            "matched_rule_ids": plan["matched_rule_ids"],
        },
    )
    ended_at = utc_now()
    append_jsonl(
        files["adapter_events"],
        {
            "adapter_id": adapter_id,
            "event": "run",
            "mode": "live",
            "outcome": outcome,
            "timestamp": ended_at,
        },
    )
    return RunExecution(
        adapter_outcome=outcome,
        started_at=started_at,
        ended_at=ended_at,
        exit_code=125,
        stdout_path=files["stdout"],
        stderr_path=files["stderr"],
        adapter_events_path=files["adapter_events"],
    )


def _record_workspace_diff(
    files: dict[str, Path],
    workspace_path: Path,
    before: dict[str, dict[str, Any]],
    canary_labels: list[str],
) -> None:
    after = snapshot_tree(workspace_path)
    for observation in diff_snapshots(before, after):
        if _is_adapter_instrumentation_path(observation["path"]):
            continue
        file_path = workspace_path / observation["path"].removeprefix("./")
        labels = []
        if file_path.exists() and file_path.is_file():
            labels = scan_text_for_canaries(file_path.read_text(encoding="utf-8", errors="replace"), canary_labels)
        observation["canary_labels"] = labels
        observation["timestamp"] = utc_now()
        append_jsonl(files["file_write_events"], observation)
        append_jsonl(files["file_observations"], observation)
        if labels:
            append_jsonl(
                files["canary_hits"],
                {
                    "event": "canary.observe",
                    "labels": labels,
                    "path": observation["path"],
                    "sink_type": "docker_output_file",
                    "timestamp": utc_now(),
                },
            )


def _record_log_canaries(
    files: dict[str, Path],
    stdout: str,
    stderr: str,
    canary_labels: list[str],
) -> None:
    for sink_type, content, ref in [
        ("stdout_log", stdout, str(files["stdout"])),
        ("stderr_log", stderr, str(files["stderr"])),
    ]:
        labels = scan_text_for_canaries(content, canary_labels)
        if labels:
            append_jsonl(
                files["canary_hits"],
                {
                    "event": "canary.observe",
                    "labels": labels,
                    "path": ref,
                    "sink_type": sink_type,
                    "timestamp": utc_now(),
                },
            )


def _profile_command_decision(command: list[str], runtime_profile: dict[str, Any]) -> tuple[bool, list[str]]:
    shell = runtime_profile["features"]["shell"]
    if not command:
        return False, ["no command provided"]
    executable = Path(command[0]).name
    if not shell["enabled"]:
        return False, ["profile disables shell execution"]
    denied = shell.get("denied_executables", [])
    if "*" in denied or executable in denied or command[0] in denied:
        return False, [f"profile denies executable {executable}"]
    allowed = shell.get("allowed_executables", [])
    if executable not in allowed and command[0] not in allowed:
        return False, [f"profile does not allow executable {executable}"]
    return True, [f"profile allows executable {executable}"]


def _contract_command_decision(command: list[str], contract: dict[str, Any]) -> tuple[bool, list[str], list[str]]:
    if not command:
        return False, ["no command provided"], []
    shell_rules = contract.get("access", {}).get("shell", {})
    deny_rules = shell_rules.get("deny", [])
    allow_rules = shell_rules.get("allow", [])
    matched_rule_ids: list[str] = []
    for rule in deny_rules:
        if _command_rule_matches(rule.get("match", {}), command):
            return False, [f"contract denies shell command via {rule.get('id')}"], [rule.get("id", "")]
    if allow_rules:
        for rule in allow_rules:
            if _command_rule_matches(rule.get("match", {}), command):
                matched_rule_ids.append(rule.get("id", ""))
        if not matched_rule_ids:
            return False, ["contract has shell allow rules but none matched command"], []
        return True, ["contract allows shell command"], matched_rule_ids
    return True, ["contract has no shell allow rules and no deny match"], []


def _command_rule_matches(match: dict[str, Any], command: list[str]) -> bool:
    if "argv_exact" in match:
        return command == match["argv_exact"]
    if "argv_prefix" in match:
        prefix = match["argv_prefix"]
        return command[: len(prefix)] == prefix
    if "executable" in match:
        executable = Path(command[0]).name if command else ""
        pattern = match["executable"]
        return pattern == "*" or executable == pattern or command[0] == pattern
    return False


def _image_decision(
    runtime_profile: dict[str, Any],
    constraints: dict[str, Any],
) -> tuple[bool, list[str]]:
    image_ref = constraints.get("container_image_ref", "")
    digest = _image_digest(image_ref)
    if not digest:
        return False, ["container image is not pinned by sha256 digest"]
    expected_digest = runtime_profile.get("reproducibility", {}).get("base_image_digest")
    if expected_digest and digest != expected_digest:
        return False, ["container image digest does not match profile reproducibility.base_image_digest"]
    return True, ["container image is pinned and matches profile constraints"]


def _image_digest(image_ref: str) -> str:
    if image_ref.startswith("sha256:"):
        return image_ref
    if "@sha256:" not in image_ref:
        return ""
    return "sha256:" + image_ref.rsplit("@sha256:", 1)[1]


def _synthetic_env(runtime_profile: dict[str, Any]) -> dict[str, str]:
    credentials = runtime_profile["features"]["credentials"]
    env_allowlist = set(credentials.get("env_allowlist", []))
    synthetic: dict[str, str] = {}
    for name in credentials.get("synthetic_credentials", []):
        if name in env_allowlist:
            synthetic[name] = f"synthetic_{name.lower()}"
    roots = runtime_profile["features"]["filesystem"].get("roots", [])
    for root in roots:
        root_id = root.get("id")
        mount_point = root.get("mount_point")
        if root_id == "repo" and "SKILLDIFF_REPO_ROOT" in env_allowlist and isinstance(mount_point, str):
            synthetic["SKILLDIFF_REPO_ROOT"] = mount_point
        if root_id == "out" and "SKILLDIFF_OUTPUT_ROOT" in env_allowlist and isinstance(mount_point, str):
            synthetic["SKILLDIFF_OUTPUT_ROOT"] = mount_point
    return synthetic


def _container_workdir(runtime_profile: dict[str, Any], mounts: list[dict[str, Any]]) -> str:
    for mount in mounts:
        if mount["mode"] == "read_write":
            return mount["target"]
    for root in runtime_profile["features"]["filesystem"].get("roots", []):
        if root.get("id") == "out":
            return root.get("mount_point", "/workspace/out")
    return "/workspace/out"


def _tmpfs_mounts(runtime_profile: dict[str, Any]) -> list[str]:
    targets = []
    for root in runtime_profile["features"]["filesystem"].get("roots", []):
        if root.get("id") == "tmp" and root.get("mode") == "read_write":
            mount_point = root.get("mount_point")
            if isinstance(mount_point, str):
                targets.append(mount_point)
    return targets


def _read_container_id(path: Path) -> str | None:
    if not path.exists():
        return None
    value = path.read_text(encoding="utf-8").strip()
    return value or None


def _docker_connection_failed(message: str) -> bool:
    lowered = message.lower()
    return (
        "failed to connect to the docker api" in lowered
        or "cannot connect to the docker daemon" in lowered
        or "is the docker daemon running" in lowered
    )


def _docker_executable() -> str | None:
    configured = os.environ.get("DOCKER_BIN")
    if configured:
        return configured if Path(configured).exists() and os.access(configured, os.X_OK) else None
    found = shutil.which("docker")
    if found:
        return found
    for candidate in [
        "/usr/local/bin/docker",
        "/opt/homebrew/bin/docker",
        "/Applications/Docker.app/Contents/Resources/bin/docker",
    ]:
        if Path(candidate).exists():
            return candidate
    return None


def _container_invocation_with_docker_path(invocation: list[str], docker_path: str) -> list[str]:
    if not invocation:
        return invocation
    resolved = list(invocation)
    if Path(resolved[0]).name == "docker":
        resolved[0] = docker_path
    return resolved


def _generated_outputs(workspace_path: Path) -> list[dict[str, Any]]:
    outputs = []
    if not workspace_path.exists():
        return outputs
    for path in sorted(workspace_path.rglob("*")):
        if path.is_file():
            rel_path = "./" + path.relative_to(workspace_path).as_posix()
            if _is_adapter_instrumentation_path(rel_path):
                continue
            outputs.append(
                {
                    "path": rel_path,
                    "size": path.stat().st_size,
                }
            )
    return outputs


def _is_adapter_instrumentation_path(path: str) -> bool:
    return (
        path == "./.skilldiff_file_read_events.jsonl"
        or path == "./.skilldiff_file_write_events.jsonl"
        or path == "./.skilldiff_network_events.jsonl"
        or path == "./.skilldiff_network_sink_requests.jsonl"
        or path == "./.skilldiff_strace_file_reads.log"
        or path.startswith("./.skilldiff_provenance/")
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _is_controlled_python_command(command: list[str]) -> bool:
    if not command:
        return False
    return Path(command[0]).name in {"python", "python3"}


def _read_provenance_config(
    command: list[str],
    runtime_profile: dict[str, Any],
    output_workspace_path: Path,
) -> dict[str, Any]:
    syscall_enabled = runtime_profile["features"]["instrumentation"].get("file_monitor") == "syscall_container_strace"
    network_monitor = runtime_profile["features"]["instrumentation"].get("network_monitor")
    network_enabled = _is_controlled_python_command(command) and network_monitor in {
        "shimmed_fake_sink",
        "disabled_network_assertion",
    }
    python_enabled = _is_controlled_python_command(command) and not syscall_enabled
    python_shim_enabled = python_enabled or network_enabled
    host_shim_dir = output_workspace_path / ".skilldiff_provenance"
    host_event_path = output_workspace_path / ".skilldiff_file_read_events.jsonl"
    host_write_event_path = output_workspace_path / ".skilldiff_file_write_events.jsonl"
    host_network_event_path = output_workspace_path / ".skilldiff_network_events.jsonl"
    host_network_sink_requests_path = output_workspace_path / ".skilldiff_network_sink_requests.jsonl"
    host_strace_log_path = output_workspace_path / ".skilldiff_strace_file_reads.log"
    if python_shim_enabled:
        _install_python_read_provenance_shim(host_shim_dir)
    network_policy = runtime_profile["features"]["network"]
    return {
        "enabled": python_enabled or syscall_enabled or network_enabled,
        "python_enabled": python_enabled,
        "python_shim_enabled": python_shim_enabled,
        "syscall_enabled": syscall_enabled,
        "network_enabled": network_enabled,
        "network_mode": "block" if not network_policy.get("enabled") else "fake_sink",
        "fake_sink_domains": network_policy.get("fake_sink_domains", []),
        "instrumentation_model": "container_strace_mvp" if syscall_enabled else "python_sitecustomize_wrapper_mvp",
        "host_event_path": str(host_event_path),
        "host_write_event_path": str(host_write_event_path),
        "host_network_event_path": str(host_network_event_path),
        "host_network_sink_requests_path": str(host_network_sink_requests_path),
        "host_shim_dir": str(host_shim_dir),
        "host_strace_log_path": str(host_strace_log_path),
        "container_event_path": "/workspace/out/.skilldiff_file_read_events.jsonl",
        "container_write_event_path": "/workspace/out/.skilldiff_file_write_events.jsonl",
        "container_network_event_path": "/workspace/out/.skilldiff_network_events.jsonl",
        "container_network_sink_requests_path": "/workspace/out/.skilldiff_network_sink_requests.jsonl",
        "container_shim_dir": "/workspace/out/.skilldiff_provenance",
        "container_strace_log_path": "/workspace/out/.skilldiff_strace_file_reads.log",
    }


def _file_read_provenance_label(read_provenance: dict[str, Any]) -> str:
    if read_provenance.get("syscall_enabled"):
        return "container_strace_mvp"
    if read_provenance.get("python_enabled"):
        return "python_sitecustomize_wrapper_mvp"
    return "not_available"


def _initial_instrumentation_status(adapter_id: str, read_provenance: dict[str, Any]) -> dict[str, Any]:
    warnings = [
        "network monitoring records Docker network policy, not full packet interception",
    ]
    network_provenance = "docker_network_none_no_packet_capture"
    if read_provenance.get("network_enabled"):
        network_provenance = "python_network_shim_mvp_plus_docker_network_none_no_packet_capture"
        warnings = [
            "network events are produced by a Python urllib shim for controlled benchmark runs, not packet capture",
            *warnings,
        ]
    if read_provenance.get("python_shim_enabled"):
        warnings = [
            "failed Python write attempts are wrapper-level evidence for controlled Python runs only",
            *warnings,
        ]
    if read_provenance.get("syscall_enabled"):
        warnings = [
            "container_strace_mvp records open/openat/openat2 events for RP3 container commands when enabled",
            "container_strace_mvp is Linux-container syscall evidence, not host-wide commercial runtime tracing",
            "metadata-only probes and unusual direct syscalls may require parser extensions beyond this MVP",
            *warnings,
        ]
    elif read_provenance.get("python_enabled"):
        warnings = [
            "filesystem.read events are MVP wrapper-level provenance for controlled Python runs only",
            "non-Python reads and Python runs that disable sitecustomize are outside this MVP instrumentation",
            *warnings,
        ]
    return {
        "adapter_id": adapter_id,
        "file_read_provenance": _file_read_provenance_label(read_provenance),
        "file_write_provenance": "pre_post_diff_plus_python_failed_write_wrapper_mvp",
        "network_provenance": network_provenance,
        "process_provenance": "docker_subprocess_wrapper",
        "trace_valid": True,
        "warnings": warnings,
    }


def _mark_file_read_provenance_unavailable(
    files: dict[str, Path],
    plan: dict[str, Any],
    reason: str,
) -> None:
    provenance = plan.get("read_provenance") or {}
    if not provenance.get("syscall_enabled"):
        return
    status_path = files["instrumentation_status"]
    status = {}
    if status_path.exists():
        status = json.loads(status_path.read_text(encoding="utf-8"))
    warnings = list(status.get("warnings", []))
    unavailable_reason = f"container_strace_mvp unavailable: {reason}"
    if unavailable_reason not in warnings:
        warnings.append(unavailable_reason)
    status.update(
        {
            "file_read_provenance": "container_strace_mvp_unavailable",
            "trace_valid": False,
            "warnings": warnings,
        }
    )
    write_json(status_path, status)
    append_jsonl(
        files["adapter_events"],
        {
            "event": "instrumentation.failure",
            "instrumentation_model": "container_strace_mvp",
            "reason": reason,
            "status": "failed",
            "timestamp": utc_now(),
        },
    )


def _instrumented_container_command(command: list[str], read_provenance: dict[str, Any]) -> list[str]:
    if not read_provenance.get("syscall_enabled") or not command:
        return command
    return [
        "strace",
        "-f",
        "-qq",
        "-e",
        "trace=open,openat,openat2",
        "-s",
        "4096",
        "-o",
        read_provenance["container_strace_log_path"],
        "--",
        *command,
    ]


def _fake_sink_url(read_provenance: dict[str, Any]) -> str:
    domains = read_provenance.get("fake_sink_domains", [])
    if not domains:
        return ""
    return f"http://{domains[0]}/skilldiff-fake-sink"


def _install_python_read_provenance_shim(shim_dir: Path) -> Path:
    shim_dir.mkdir(parents=True, exist_ok=True)
    (shim_dir / "sitecustomize.py").write_text(_CONTROLLED_PYTHON_PROVENANCE_SHIM, encoding="utf-8")
    return shim_dir


def _prepend_path_env(value: str, existing: str, *, separator: str = os.pathsep) -> str:
    if not existing:
        return value
    return value + separator + existing


def _merge_python_read_provenance_events(files: dict[str, Path], plan: dict[str, Any]) -> None:
    provenance = plan.get("read_provenance") or {}
    if not provenance.get("python_enabled"):
        return
    event_path = Path(provenance["host_event_path"])
    if not event_path.exists():
        return
    for row in _read_jsonl(event_path):
        translated = dict(row)
        path = translated.get("path")
        if isinstance(path, str):
            contract_path = _container_path_to_contract_path(path, plan.get("mounts", []))
            if contract_path != path:
                translated["original_path"] = path
                translated["path"] = contract_path
        append_jsonl(files["file_read_events"], translated)


def _merge_python_write_provenance_events(files: dict[str, Path], plan: dict[str, Any]) -> None:
    provenance = plan.get("read_provenance") or {}
    if not provenance.get("python_shim_enabled"):
        return
    event_path = Path(provenance["host_write_event_path"])
    if not event_path.exists():
        return
    for row in _read_jsonl(event_path):
        translated = dict(row)
        path = translated.get("path")
        if isinstance(path, str):
            contract_path = _container_path_to_contract_path(path, plan.get("mounts", []))
            if contract_path != path:
                translated["original_path"] = path
                translated["path"] = contract_path
        append_jsonl(files["file_write_events"], translated)
        append_jsonl(files["file_observations"], translated)


def _merge_python_network_events(files: dict[str, Path], plan: dict[str, Any]) -> None:
    provenance = plan.get("read_provenance") or {}
    if not provenance.get("network_enabled"):
        return
    event_path = Path(provenance["host_network_event_path"])
    if not event_path.exists():
        return
    for row in _read_jsonl(event_path):
        append_jsonl(files["network_events"], row)


def _merge_python_network_sink_requests(files: dict[str, Path], plan: dict[str, Any]) -> None:
    provenance = plan.get("read_provenance") or {}
    if not provenance.get("network_enabled"):
        return
    event_path = Path(provenance["host_network_sink_requests_path"])
    if not event_path.exists():
        return
    for row in _read_jsonl(event_path):
        append_jsonl(files["network_sink_requests"], row)


_STRACE_OPEN_RE = re.compile(
    r'^(?:(?P<pid>\d+)\s+)?(?P<syscall>open|openat|openat2)\((?P<args>.*)\)\s+=\s+(?P<result>.+)$'
)


def _merge_syscall_read_provenance_events(files: dict[str, Path], plan: dict[str, Any]) -> None:
    provenance = plan.get("read_provenance") or {}
    if not provenance.get("syscall_enabled"):
        return
    event_path = Path(provenance["host_strace_log_path"])
    if not event_path.exists():
        _mark_file_read_provenance_unavailable(files, plan, "strace log was not produced")
        return
    for row in _parse_strace_file_read_events(event_path, plan.get("mounts", [])):
        append_jsonl(files["file_read_events"], row)


def _parse_strace_file_read_events(path: Path, mounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            row = _parse_strace_file_read_line(line.strip(), mounts)
            if row is not None:
                rows.append(row)
    return rows


def _parse_strace_file_read_line(line: str, mounts: list[dict[str, Any]]) -> dict[str, Any] | None:
    match = _STRACE_OPEN_RE.match(line)
    if not match:
        return None
    args = match.group("args")
    opened_path = _first_quoted_path(args)
    if opened_path is None or not _is_read_open_args(args):
        return None
    result = match.group("result")
    status = "failed" if result.startswith("-1 ") else "succeeded"
    translated_path = _container_path_to_contract_path(opened_path, mounts)
    row: dict[str, Any] = {
        "event": "filesystem.read",
        "instrumentation_model": "container_strace_mvp",
        "operation": "read",
        "path": translated_path,
        "status": status,
        "timestamp": utc_now(),
        "source": "strace",
        "syscall": match.group("syscall"),
        "raw_result": result,
    }
    if translated_path != opened_path:
        row["original_path"] = opened_path
    if match.group("pid"):
        row["pid"] = int(match.group("pid"))
    if status == "failed":
        errno = result.split(maxsplit=2)[1] if len(result.split(maxsplit=2)) >= 2 else "UNKNOWN"
        row["error_type"] = errno
    return row


def _first_quoted_path(args: str) -> str | None:
    for value in re.findall(r'"((?:\\.|[^"\\])*)"', args):
        decoded = bytes(value, "utf-8").decode("unicode_escape")
        if decoded.startswith(("/", "./", "../", "~")):
            return decoded
    return None


def _is_read_open_args(args: str) -> bool:
    return not any(flag in args for flag in ("O_WRONLY", "O_RDWR", "O_CREAT", "O_TRUNC", "O_APPEND"))


def _container_path_to_contract_path(path: str, mounts: list[dict[str, Any]]) -> str:
    for mount in sorted(mounts, key=lambda item: len(str(item.get("target", ""))), reverse=True):
        target = str(mount.get("target", "")).rstrip("/")
        if not target:
            continue
        if path != target and not path.startswith(target + "/"):
            continue
        suffix = path[len(target) :].lstrip("/")
        if target == "/workspace/repo":
            return "./" + suffix if suffix else "."
        if target == "/workspace/out":
            return "./" + suffix if suffix else "."
    return path


_PYTHON_READ_PROVENANCE_SHIM = textwrap.dedent(
    r'''
    """SkillDiff MVP Python read-provenance shim.

    This records Python-level file open attempts for controlled benchmark runs.
    It is not syscall-complete tracing.
    """

    from __future__ import annotations

    import builtins
    import json
    import os
    import pathlib
    import threading
    from datetime import datetime, timezone


    _EVENTS_PATH = os.environ.get("SKILLDIFF_FILE_READ_EVENTS")
    _MODEL = os.environ.get("SKILLDIFF_READ_PROVENANCE_MODEL", "python_sitecustomize_wrapper_mvp")
    _LOCK = threading.Lock()
    _ORIGINAL_OPEN = builtins.open
    _ORIGINAL_PATH_OPEN = pathlib.Path.open


    def _utc_now():
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


    def _is_read_mode(mode):
        mode = mode or "r"
        return "r" in mode and not any(flag in mode for flag in ("w", "a", "x"))


    def _target(path):
        try:
            return os.fspath(path)
        except TypeError:
            return str(path)


    def _append_event(path, status, mode, error=None):
        if not _EVENTS_PATH:
            return
        row = {
            "event": "filesystem.read",
            "instrumentation_model": _MODEL,
            "operation": "read",
            "path": _target(path),
            "status": status,
            "timestamp": _utc_now(),
            "mode": mode or "r",
        }
        if error is not None:
            row["error_type"] = type(error).__name__
            row["error_message"] = str(error)
        with _LOCK:
            with _ORIGINAL_OPEN(_EVENTS_PATH, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, sort_keys=True) + "\n")


    def _open(path, mode="r", *args, **kwargs):
        if not _is_read_mode(mode):
            return _ORIGINAL_OPEN(path, mode, *args, **kwargs)
        try:
            handle = _ORIGINAL_OPEN(path, mode, *args, **kwargs)
        except Exception as exc:
            _append_event(path, "failed", mode, exc)
            raise
        _append_event(path, "succeeded", mode)
        return handle


    def _path_open(self, mode="r", buffering=-1, encoding=None, errors=None, newline=None):
        if not _is_read_mode(mode):
            return _ORIGINAL_PATH_OPEN(self, mode, buffering, encoding, errors, newline)
        try:
            handle = _ORIGINAL_PATH_OPEN(self, mode, buffering, encoding, errors, newline)
        except Exception as exc:
            _append_event(self, "failed", mode, exc)
            raise
        _append_event(self, "succeeded", mode)
        return handle


    builtins.open = _open
    pathlib.Path.open = _path_open
    '''
).lstrip()


def _hash_json(value: Any) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def _hash_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()
