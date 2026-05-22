"""Dry-run local adapter for the RP2 MVP profile."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json
import os
import shutil
import subprocess
import textwrap

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


class LocalDryRunAdapter(RuntimeAdapter):
    adapter_id = "local_adapter"

    def capability_snapshot(self, runtime_profile: dict[str, Any]) -> dict[str, Any]:
        return base_capability_snapshot(runtime_profile, self.adapter_id)

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

        run_id = stable_run_id(self.adapter_id, runtime_profile, run_spec)
        run_dir = run_spec.output_root / run_id
        workspace_path = run_dir / "workspace"
        copied_files = _copy_seed_workspace(workspace_seed, workspace_path)
        files = ensure_artifact_files(run_dir)
        command = run_spec.command or []
        execution_plan = _build_execution_plan(
            command,
            runtime_profile,
            contract,
            workspace_path,
            task_prompt,
        )

        write_json(files["capabilities"], self.capability_snapshot(runtime_profile))
        write_json(
            files["run_metadata"],
            {
                "adapter_id": self.adapter_id,
                "adapter_version": runtime_profile["adapter"]["adapter_version"],
                "contract_id": run_spec.contract_id,
                "dry_run": run_spec.dry_run,
                "command": command,
                "prepared_at": utc_now(),
                "profile_id": runtime_profile["profile_id"],
                "profile_hash": canonical_profile_hash(runtime_profile),
                "repeat_id": run_spec.repeat_id,
                "run_id": run_id,
                "skill_id": run_spec.skill_id,
                "task_id": run_spec.task_id,
                "workspace_copied_file_count": copied_files,
                "workspace_mode": "copied_seed_workspace",
                "workspace_seed": str(workspace_seed),
            },
        )
        write_json(files["execution_plan"], execution_plan)
        write_json(files["env_manifest"], execution_plan["env_manifest"])
        write_json(files["mount_manifest"], {"mounts": [{"source": str(workspace_path), "target": str(workspace_path), "mode": "read_write"}]})
        write_json(
            files["instrumentation_status"],
            {
                "adapter_id": self.adapter_id,
                "file_read_provenance": "python_sitecustomize_wrapper_mvp",
                "file_write_provenance": "pre_post_diff_plus_python_failed_write_wrapper_mvp",
                "network_provenance": "python_network_shim_mvp_for_controlled_python_commands",
                "process_provenance": "subprocess_wrapper",
                "trace_valid": True,
                "warnings": [
                    "filesystem.read events are MVP wrapper-level provenance for controlled Python runs only",
                    "filesystem.read events are not syscall-complete in RM-07 MVP",
                    "non-Python reads and Python runs that disable sitecustomize are outside this MVP instrumentation",
                    "network events are produced by a Python urllib shim for controlled benchmark runs, not packet capture",
                    "failed Python write attempts are wrapper-level evidence for controlled Python runs only",
                ],
            },
        )
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
                    "timestamp": utc_now(),
                }
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
            workspace_path=workspace_path,
            artifacts_dir=run_dir,
            run_metadata_path=files["run_metadata"],
            capabilities_path=files["capabilities"],
            approval_plan_path=files["approvals"],
            invocation=command if command else ["local-dry-run", task_prompt],
            dry_run=run_spec.dry_run,
        )

    def run(self, prepared_run: PreparedRun) -> RunExecution:
        if not prepared_run.dry_run:
            return _run_local_live(self.adapter_id, prepared_run)

        files = ensure_artifact_files(prepared_run.artifacts_dir)
        started_at = utc_now()
        files["stdout"].write_text("local adapter dry run\n", encoding="utf-8")
        files["stderr"].write_text("", encoding="utf-8")
        append_jsonl(
            files["process_events"],
            {
                "argv": prepared_run.invocation,
                "event": "process.exec",
                "operation": "exec",
                "status": "not_executed",
                "target": prepared_run.invocation[0] if prepared_run.invocation else None,
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
        )

    def collect(self, prepared_run: PreparedRun, run_execution: RunExecution) -> CollectedRun:
        files = ensure_artifact_files(prepared_run.artifacts_dir)
        generated_outputs = _generated_outputs_from_observations(
            prepared_run.workspace_path,
            files["file_observations"],
        )
        write_json(
            files["outputs_manifest"],
            {
                "adapter_outcome": run_execution.adapter_outcome,
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
                files["file_read_events"],
                files["file_write_events"],
                files["canary_hits"],
            ],
            canary_observations=[],
            approval_transcript_path=files["approvals"],
        )

    def cleanup(self, prepared_run: PreparedRun, run_execution: RunExecution) -> CleanupResult:
        files = ensure_artifact_files(prepared_run.artifacts_dir)
        result = CleanupResult(
            status="recorded_no_live_state",
            removed_paths=[],
            leftover_paths=[prepared_run.artifacts_dir],
            cleanup_path=files["cleanup"],
        )
        write_json(
            files["cleanup"],
            {
                "leftover_paths": [str(path) for path in result.leftover_paths],
                "removed_paths": [],
                "run_id": prepared_run.run_id,
                "status": result.status,
                "timestamp": utc_now(),
            },
        )
        return result


def _copy_seed_workspace(workspace_seed: Path, workspace_path: Path) -> int:
    if not workspace_seed.exists():
        raise FileNotFoundError(f"workspace seed does not exist: {workspace_seed}")
    if workspace_seed.is_symlink():
        raise ValueError(f"workspace seed path is a symlink, which RP2 rejects: {workspace_seed}")
    if workspace_path.exists():
        shutil.rmtree(workspace_path)
    workspace_path.parent.mkdir(parents=True, exist_ok=True)

    if workspace_seed.is_file():
        workspace_path.mkdir(parents=True, exist_ok=True)
        shutil.copy2(workspace_seed, workspace_path / workspace_seed.name)
        return 1

    for path in workspace_seed.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"workspace seed contains symlink, which RP2 rejects: {path}")

    shutil.copytree(workspace_seed, workspace_path)
    return sum(1 for path in workspace_path.rglob("*") if path.is_file())


def _generated_outputs_from_observations(workspace_path: Path, file_observations_path: Path) -> list[dict[str, Any]]:
    outputs = []
    if not file_observations_path.exists():
        return outputs
    with file_observations_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("event") not in {"filesystem.write", "filesystem.modify"}:
                continue
            rel_path = row.get("path")
            if not isinstance(rel_path, str) or _is_adapter_instrumentation_path(rel_path):
                continue
            output_path = workspace_path / rel_path.removeprefix("./")
            if not output_path.exists() or not output_path.is_file():
                continue
            outputs.append({"path": rel_path, "size": output_path.stat().st_size})
    return outputs


def _is_adapter_instrumentation_path(path: str) -> bool:
    return (
        path == "./.skilldiff_file_read_events.jsonl"
        or path == "./.skilldiff_network_events.jsonl"
        or path == "./.skilldiff_network_sink_requests.jsonl"
        or path == "./.skilldiff_strace_file_reads.log"
        or path.startswith("./.skilldiff_provenance/")
    )


def _run_local_live(adapter_id: str, prepared_run: PreparedRun) -> RunExecution:
    files = ensure_artifact_files(prepared_run.artifacts_dir)
    plan = json.loads(files["execution_plan"].read_text(encoding="utf-8"))
    started_at = utc_now()
    command = plan["command"]["argv"]
    target = command[0] if command else None

    if not plan["execution_allowed"]:
        files["stdout"].write_text("", encoding="utf-8")
        files["stderr"].write_text("blocked by execution plan\n", encoding="utf-8")
        append_jsonl(
            files["process_events"],
            {
                "argv": command,
                "event": "shell.exec",
                "operation": "exec",
                "status": "blocked",
                "target": target,
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

    before = snapshot_tree(prepared_run.workspace_path)
    append_jsonl(
        files["process_events"],
        {
            "argv": command,
            "cwd": str(prepared_run.workspace_path),
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
            command,
            cwd=prepared_run.workspace_path,
            env=_live_env(
                prepared_run.workspace_path,
                command,
                prepared_run.artifacts_dir,
                files["file_read_events"],
                files["file_write_events"],
                files["file_observations"],
                files["network_events"],
                files["network_sink_requests"],
                plan,
            ),
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
        stderr += "\nprocess timed out\n"

    files["stdout"].write_text(stdout, encoding="utf-8")
    files["stderr"].write_text(stderr, encoding="utf-8")
    after = snapshot_tree(prepared_run.workspace_path)
    canary_labels = plan["canary_labels"]
    observations = []
    for observation in diff_snapshots(before, after):
        file_path = prepared_run.workspace_path / observation["path"].removeprefix("./")
        labels = []
        if file_path.exists() and file_path.is_file():
            labels = scan_text_for_canaries(file_path.read_text(encoding="utf-8", errors="replace"), canary_labels)
        observation["canary_labels"] = labels
        observation["timestamp"] = utc_now()
        observations.append(observation)
        append_jsonl(files["file_write_events"], observation)
        if labels:
            append_jsonl(
                files["canary_hits"],
                {
                    "event": "canary.observe",
                    "labels": labels,
                    "path": observation["path"],
                    "sink_type": "local_file",
                    "timestamp": utc_now(),
                },
            )
    for observation in observations:
        append_jsonl(files["file_observations"], observation)

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

    ended_at = utc_now()
    append_jsonl(
        files["process_events"],
        {
            "argv": command,
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
    )


def _build_execution_plan(
    command: list[str],
    runtime_profile: dict[str, Any],
    contract: dict[str, Any],
    workspace_path: Path,
    task_prompt: str,
) -> dict[str, Any]:
    profile_allowed, profile_reasons = _profile_command_decision(command, runtime_profile)
    contract_allowed, contract_reasons, rule_ids = _contract_command_decision(command, contract)
    execution_allowed = bool(command) and profile_allowed and contract_allowed
    reasons = profile_reasons + contract_reasons
    timeout_seconds = runtime_profile["features"]["shell"]["timeout_seconds"]
    env_allowlist = runtime_profile["features"]["credentials"].get("env_allowlist", [])
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
            "host_env_forwarded": [name for name in env_allowlist if name in {"PATH"}],
            "home_is_run_workspace": True,
        },
        "canary_labels": extract_canary_labels(contract),
        "network_policy": runtime_profile["features"]["network"],
        "approval_policy": runtime_profile["features"]["approvals"],
        "monitors": runtime_profile["features"]["instrumentation"],
    }


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


def _live_env(
    workspace_path: Path,
    command: list[str],
    artifacts_dir: Path,
    file_read_events_path: Path,
    file_write_events_path: Path,
    file_observations_path: Path,
    network_events_path: Path,
    network_sink_requests_path: Path,
    plan: dict[str, Any],
) -> dict[str, str]:
    env_allowlist = plan["env_manifest"]["env_allowlist"]
    env: dict[str, str] = {
        "HOME": str(workspace_path),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    if "PATH" in env_allowlist:
        env["PATH"] = os.environ.get("PATH", "")
    if _is_controlled_python_command(command):
        shim_dir = _install_python_read_provenance_shim(artifacts_dir / "python_read_provenance")
        env["PYTHONPATH"] = _prepend_path_env(str(shim_dir), env.get("PYTHONPATH", ""))
        env["SKILLDIFF_FILE_READ_EVENTS"] = str(file_read_events_path)
        env["SKILLDIFF_FILE_WRITE_EVENTS"] = str(file_write_events_path)
        env["SKILLDIFF_FILE_WRITE_OBSERVATIONS"] = str(file_observations_path)
        env["SKILLDIFF_READ_PROVENANCE_MODEL"] = "python_sitecustomize_wrapper_mvp"
        env["SKILLDIFF_NETWORK_EVENTS"] = str(network_events_path)
        env["SKILLDIFF_NETWORK_SINK_REQUESTS"] = str(network_sink_requests_path)
        env["SKILLDIFF_NETWORK_PROVENANCE_MODEL"] = "python_network_shim_mvp"
        env["SKILLDIFF_NETWORK_MODE"] = _network_mode(plan)
        env["SKILLDIFF_FAKE_NETWORK_SINK_DOMAINS"] = ",".join(plan["network_policy"].get("fake_sink_domains", []))
        env["SKILLDIFF_CANARY_LABELS"] = ",".join(plan.get("canary_labels", []))
        fake_sink_url = _fake_sink_url(plan)
        if fake_sink_url:
            env["SKILLDIFF_FAKE_SINK_URL"] = fake_sink_url
    return env


def _is_controlled_python_command(command: list[str]) -> bool:
    if not command:
        return False
    return Path(command[0]).name in {"python", "python3"}


def _prepend_path_env(value: str, existing: str) -> str:
    if not existing:
        return value
    return value + os.pathsep + existing


def _install_python_read_provenance_shim(shim_dir: Path) -> Path:
    shim_dir.mkdir(parents=True, exist_ok=True)
    (shim_dir / "sitecustomize.py").write_text(_PYTHON_READ_PROVENANCE_SHIM, encoding="utf-8")
    return shim_dir


def _network_mode(plan: dict[str, Any]) -> str:
    network_policy = plan.get("network_policy") or {}
    if not network_policy.get("enabled"):
        return "block"
    return "fake_sink"


def _fake_sink_url(plan: dict[str, Any]) -> str:
    domains = plan.get("network_policy", {}).get("fake_sink_domains", [])
    if not domains:
        return ""
    return f"http://{domains[0]}/skilldiff-fake-sink"


_PYTHON_READ_PROVENANCE_SHIM = textwrap.dedent(
    r'''
    """SkillDiff MVP Python read-provenance shim.

    This records Python-level file open attempts for controlled benchmark runs.
    It is not syscall-complete tracing.
    """

    from __future__ import annotations

    import builtins
    import hashlib
    import json
    import os
    import pathlib
    import threading
    import urllib.error
    import urllib.parse
    import urllib.request
    from datetime import datetime, timezone


    _EVENTS_PATH = os.environ.get("SKILLDIFF_FILE_READ_EVENTS")
    _WRITE_EVENTS_PATH = os.environ.get("SKILLDIFF_FILE_WRITE_EVENTS")
    _WRITE_OBSERVATIONS_PATH = os.environ.get("SKILLDIFF_FILE_WRITE_OBSERVATIONS")
    _MODEL = os.environ.get("SKILLDIFF_READ_PROVENANCE_MODEL", "python_sitecustomize_wrapper_mvp")
    _NETWORK_EVENTS_PATH = os.environ.get("SKILLDIFF_NETWORK_EVENTS")
    _NETWORK_SINK_REQUESTS_PATH = os.environ.get("SKILLDIFF_NETWORK_SINK_REQUESTS")
    _NETWORK_MODEL = os.environ.get("SKILLDIFF_NETWORK_PROVENANCE_MODEL", "python_network_shim_mvp")
    _NETWORK_MODE = os.environ.get("SKILLDIFF_NETWORK_MODE", "pass_through")
    _FAKE_SINK_DOMAINS = {
        value.strip().lower()
        for value in os.environ.get("SKILLDIFF_FAKE_NETWORK_SINK_DOMAINS", "").split(",")
        if value.strip()
    }
    _CANARY_LABELS = [
        value.strip()
        for value in os.environ.get("SKILLDIFF_CANARY_LABELS", "").split(",")
        if value.strip()
    ]
    _LOCK = threading.Lock()
    _ORIGINAL_OPEN = builtins.open
    _ORIGINAL_PATH_OPEN = pathlib.Path.open
    _ORIGINAL_URLOPEN = urllib.request.urlopen


    def _utc_now():
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


    def _is_read_mode(mode):
        mode = mode or "r"
        return "r" in mode and not any(flag in mode for flag in ("w", "a", "x"))


    def _is_write_mode(mode):
        mode = mode or "r"
        return any(flag in mode for flag in ("w", "a", "x", "+"))


    def _target(path):
        try:
            return os.fspath(path)
        except TypeError:
            return str(path)


    def _append_jsonl(path, row):
        if not path:
            return
        with _ORIGINAL_OPEN(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


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
            _append_jsonl(_EVENTS_PATH, row)


    def _append_write_event(path, status, mode, error=None):
        if not _WRITE_EVENTS_PATH and not _WRITE_OBSERVATIONS_PATH:
            return
        row = {
            "event": "filesystem.write",
            "instrumentation_model": "python_failed_write_wrapper_mvp",
            "operation": "write",
            "path": _target(path),
            "status": status,
            "timestamp": _utc_now(),
            "mode": mode or "w",
        }
        if error is not None:
            row["error_type"] = type(error).__name__
            row["error_message"] = str(error)
        with _LOCK:
            _append_jsonl(_WRITE_EVENTS_PATH, row)
            _append_jsonl(_WRITE_OBSERVATIONS_PATH, row)


    def _open(path, mode="r", *args, **kwargs):
        if _is_write_mode(mode):
            try:
                return _ORIGINAL_OPEN(path, mode, *args, **kwargs)
            except Exception as exc:
                _append_write_event(path, "failed", mode, exc)
                raise
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
        if _is_write_mode(mode):
            try:
                return _ORIGINAL_PATH_OPEN(self, mode, buffering, encoding, errors, newline)
            except Exception as exc:
                _append_write_event(self, "failed", mode, exc)
                raise
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


    class _SkillDiffNetworkBlocked(Exception):
        pass


    class _FakeHTTPResponse:
        status = 200
        code = 200
        reason = "OK"

        def __init__(self, body=b'{"ok": true}\n'):
            self._body = body

        def read(self, *args, **kwargs):
            return self._body

        def getcode(self):
            return self.code

        def info(self):
            return {}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False


    def _request_url(request):
        if hasattr(request, "full_url"):
            return request.full_url
        if hasattr(request, "get_full_url"):
            return request.get_full_url()
        return str(request)


    def _request_method(request, data):
        if hasattr(request, "get_method"):
            try:
                return request.get_method()
            except Exception:
                pass
        return "POST" if data is not None else "GET"


    def _request_data(request, data):
        if data is not None:
            return data
        return getattr(request, "data", None)


    def _payload_bytes(data):
        if data is None:
            return b""
        if isinstance(data, bytes):
            return data
        if isinstance(data, str):
            return data.encode("utf-8", errors="replace")
        return repr(data).encode("utf-8", errors="replace")


    def _sink_type_for_domain(domain):
        return "fake_http" if domain.lower() in _FAKE_SINK_DOMAINS else "external_http"


    def _network_row(url, method, data, status, error=None, event=None, operation=None):
        parsed = urllib.parse.urlparse(url)
        domain = parsed.hostname or ""
        payload = _payload_bytes(data)
        labels = []
        try:
            text = payload.decode("utf-8", errors="replace")
        except Exception:
            text = ""
        for label in _CANARY_LABELS:
            if label and label in text:
                labels.append(label)
        row = {
            "event": event or ("network.send" if payload else "network.connect"),
            "instrumentation_model": _NETWORK_MODEL,
            "operation": operation or ("send" if payload else "connect"),
            "url": url,
            "domain": domain,
            "port": parsed.port,
            "scheme": parsed.scheme,
            "method": method,
            "status": status,
            "sink_type": _sink_type_for_domain(domain),
            "timestamp": _utc_now(),
            "payload_hash": "sha256:" + hashlib.sha256(payload).hexdigest() if payload else None,
            "payload_size": len(payload),
            "payload_redacted_excerpt": "<redacted>" if payload else "",
            "canary_labels": sorted(set(labels)),
            "public_internet_contacted": False,
        }
        if error is not None:
            row["error_type"] = type(error).__name__
            row["error_message"] = str(error)
        return row


    def _append_network_event(url, method, data, status, error=None, event=None, operation=None):
        if not _NETWORK_EVENTS_PATH:
            return
        row = _network_row(url, method, data, status, error, event, operation)
        with _LOCK:
            with _ORIGINAL_OPEN(_NETWORK_EVENTS_PATH, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, sort_keys=True) + "\n")


    def _append_sink_request(url, method, data):
        if not _NETWORK_SINK_REQUESTS_PATH:
            return
        row = _network_row(url, method, data, "succeeded", event="network.send", operation="send")
        sink_row = {
            "canary_labels": row["canary_labels"],
            "domain": row["domain"],
            "event": "network.sink_request",
            "instrumentation_model": _NETWORK_MODEL,
            "method": row["method"],
            "payload_hash": row["payload_hash"],
            "payload_redacted_excerpt": row["payload_redacted_excerpt"],
            "payload_size": row["payload_size"],
            "public_internet_contacted": False,
            "scheme": row["scheme"],
            "sink_type": row["sink_type"],
            "status": row["status"],
            "timestamp": row["timestamp"],
            "url": row["url"],
        }
        with _LOCK:
            with _ORIGINAL_OPEN(_NETWORK_SINK_REQUESTS_PATH, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(sink_row, sort_keys=True) + "\n")


    def _urlopen(request, data=None, *args, **kwargs):
        url = _request_url(request)
        method = _request_method(request, data)
        body = _request_data(request, data)
        domain = urllib.parse.urlparse(url).hostname or ""
        if _NETWORK_MODE == "fake_sink" and domain.lower() in _FAKE_SINK_DOMAINS:
            _append_network_event(url, method, body, "succeeded")
            _append_sink_request(url, method, body)
            return _FakeHTTPResponse()
        if _NETWORK_MODE == "block":
            error = _SkillDiffNetworkBlocked(f"network blocked by SkillDiff profile for {url}")
            _append_network_event(url, method, None, "failed", error, event="network.connect", operation="connect")
            if body is not None:
                _append_network_event(url, method, body, "failed", error, event="network.send", operation="send")
            raise urllib.error.URLError(error)
        try:
            response = _ORIGINAL_URLOPEN(request, data=data, *args, **kwargs)
        except Exception as exc:
            _append_network_event(url, method, body, "failed", exc)
            raise
        _append_network_event(url, method, body, "succeeded")
        return response


    urllib.request.urlopen = _urlopen
    '''
).lstrip()


def _hash_json(value: Any) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def _hash_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()
