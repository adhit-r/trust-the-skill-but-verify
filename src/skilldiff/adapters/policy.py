"""Policy-hardened adapter for the RP6 mitigation profile.

RP6 is intentionally narrower than a product sandbox. It stages only
contract-allowed workspace inputs, executes controlled Python fixture commands,
and enforces file/network policy through a Python wrapper so the resulting trace
can distinguish blocked attempted overreach from realized violations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import fnmatch
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
    workspace_snapshot_hash,
    write_json,
    write_jsonl,
)
from skilldiff.traces.events import diff_snapshots, extract_canary_labels, scan_text_for_canaries, snapshot_tree


class HardenedPolicyAdapter(RuntimeAdapter):
    adapter_id = "hardened_policy_adapter"

    def capability_snapshot(self, runtime_profile: dict[str, Any]) -> dict[str, Any]:
        snapshot = base_capability_snapshot(runtime_profile, self.adapter_id)
        snapshot["policy_enforcement_boundary"] = {
            "command_support": "controlled_python_only",
            "filesystem": "contract_path_policy_for_workspace_paths",
            "network": "python_wrapper_network_blocker_for_controlled_python",
            "tooling": "semantic_event_policy_normalization_for_fixture_tools",
        }
        disabled_components = _ablation_disabled_components(runtime_profile)
        if disabled_components:
            snapshot["rp6_component_ablation"] = {
                "disabled_components": disabled_components,
                "boundary": "research fixture ablation only; normal RP6 report-card runs keep all controls enabled",
            }
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

        command = run_spec.command or []
        task_prompt_hash = _hash_text(task_prompt)
        workspace_hash = workspace_snapshot_hash(workspace_seed)
        run_id = stable_run_id(
            self.adapter_id,
            runtime_profile,
            run_spec,
            task_prompt_hash=task_prompt_hash,
            workspace_snapshot_hash=workspace_hash,
        )
        run_dir = run_spec.output_root / run_id
        workspace_path = run_dir / "workspace"
        files = ensure_artifact_files(run_dir)
        policy = _contract_policy(contract, workspace_path, runtime_profile)
        copied_files = _stage_contract_workspace(workspace_seed, workspace_path, policy["read_allow"])
        execution_plan = _build_execution_plan(command, runtime_profile, contract, workspace_path, task_prompt, policy)

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
                "skill_artifact": run_spec.skill_artifact,
                "skill_id": run_spec.skill_id,
                "task_id": run_spec.task_id,
                "task_prompt_hash": task_prompt_hash,
                "task_prompt_ref": run_spec.task_prompt_ref,
                "variant_id": run_spec.variant_id,
                "workspace_copied_file_count": copied_files,
                "workspace_mode": "contract_scoped_staged_workspace",
                "workspace_seed": str(workspace_seed),
                "workspace_seed_id": run_spec.workspace_seed,
                "workspace_snapshot_hash": workspace_hash,
            },
        )
        write_json(files["execution_plan"], execution_plan)
        write_json(files["env_manifest"], execution_plan["env_manifest"])
        write_json(
            files["mount_manifest"],
            {
                "mounts": [
                    {
                        "source": str(workspace_path),
                        "target": str(workspace_path),
                        "mode": "contract_scoped_read_write",
                    }
                ]
            },
        )
        write_json(
            files["instrumentation_status"],
            {
                "adapter_id": self.adapter_id,
                "file_read_provenance": "rp6_python_policy_wrapper",
                "file_write_provenance": "rp6_python_policy_wrapper",
                "network_provenance": "rp6_python_network_blocker",
                "process_provenance": "rp6_subprocess_wrapper",
                "semantic_event_policy": "rp6_fixture_tool_policy_rewriter",
                "trace_valid": True,
                "warnings": [
                    "RP6 policy enforcement is wrapper-level for controlled Python fixture commands only",
                    "outside-workspace Python runtime reads are not claimed as syscall-complete provenance",
                    "tool enforcement is normalized from controlled semantic fixture events, not live MCP enforcement",
                ],
            },
        )
        _write_empty_artifacts(files)
        write_jsonl(
            files["file_observations"],
            [
                {
                    "copied_file_count": copied_files,
                    "event": "workspace_contract_stage",
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
            invocation=command if command else ["rp6-policy-dry-run", task_prompt],
            dry_run=run_spec.dry_run,
        )

    def run(self, prepared_run: PreparedRun) -> RunExecution:
        if not prepared_run.dry_run:
            return _run_policy_live(self.adapter_id, prepared_run)

        files = ensure_artifact_files(prepared_run.artifacts_dir)
        started_at = utc_now()
        command = prepared_run.invocation
        files["stdout"].write_text("RP6 hardened policy adapter dry run\n", encoding="utf-8")
        files["stderr"].write_text("", encoding="utf-8")
        append_jsonl(
            files["process_events"],
            {
                "argv": command,
                "event": "process.exec",
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
        )

    def collect(self, prepared_run: PreparedRun, run_execution: RunExecution) -> CollectedRun:
        files = ensure_artifact_files(prepared_run.artifacts_dir)
        generated_outputs = _generated_outputs_from_observations(prepared_run.workspace_path, files["file_observations"])
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
            {"adapter_id": self.adapter_id, "event": "collect", "timestamp": utc_now()},
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
                files["semantic_events"],
                files["canary_hits"],
            ],
            canary_observations=[],
            approval_transcript_path=files["approvals"],
        )

    def cleanup(self, prepared_run: PreparedRun, run_execution: RunExecution) -> CleanupResult:
        files = ensure_artifact_files(prepared_run.artifacts_dir)
        removed_paths: list[Path] = []
        for rel in (".skill-cache", ".skilldiff-cache", "tmp"):
            target = prepared_run.workspace_path / rel
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
                removed_paths.append(Path("./") / rel)
        result = CleanupResult(
            status="recorded_contract_workspace_preserved_for_evidence",
            removed_paths=removed_paths,
            leftover_paths=[prepared_run.artifacts_dir],
            cleanup_path=files["cleanup"],
        )
        write_json(
            files["cleanup"],
            {
                "leftover_paths": [str(path) for path in result.leftover_paths],
                "removed_paths": [path.as_posix() for path in removed_paths],
                "run_id": prepared_run.run_id,
                "status": result.status,
                "timestamp": utc_now(),
            },
        )
        return result


def _write_empty_artifacts(files: dict[str, Path]) -> None:
    for key in (
        "approvals",
        "approval_events",
        "network_attempts",
        "network_events",
        "network_sink_requests",
        "process_events",
        "file_read_events",
        "file_write_events",
        "semantic_events",
        "canary_hits",
    ):
        write_jsonl(files[key], [])


def _stage_contract_workspace(workspace_seed: Path, workspace_path: Path, read_allow: list[dict[str, Any]]) -> int:
    if not workspace_seed.exists():
        raise FileNotFoundError(f"workspace seed does not exist: {workspace_seed}")
    if workspace_seed.is_symlink():
        raise ValueError(f"workspace seed path is a symlink, which RP6 rejects: {workspace_seed}")
    if workspace_path.exists():
        shutil.rmtree(workspace_path)
    workspace_path.mkdir(parents=True, exist_ok=True)

    if workspace_seed.is_file():
        rel = f"./{workspace_seed.name}"
        if _matches_any_path_rule(rel, read_allow):
            shutil.copy2(workspace_seed, workspace_path / workspace_seed.name)
            return 1
        return 0

    for path in workspace_seed.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"workspace seed contains symlink, which RP6 rejects: {path}")

    copied = 0
    for source in sorted(path for path in workspace_seed.rglob("*") if path.is_file()):
        rel = "./" + source.relative_to(workspace_seed).as_posix()
        if not _matches_any_path_rule(rel, read_allow):
            continue
        dest = workspace_path / rel.removeprefix("./")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        copied += 1
    return copied


def _run_policy_live(adapter_id: str, prepared_run: PreparedRun) -> RunExecution:
    files = ensure_artifact_files(prepared_run.artifacts_dir)
    plan = json.loads(files["execution_plan"].read_text(encoding="utf-8"))
    started_at = utc_now()
    command = plan["command"]["argv"]
    target = command[0] if command else None
    shell_approval = _approval_for_shell(plan, command)
    shell_approval_request_id = _approval_request_id(shell_approval, "shell.exec", target or "process") if shell_approval else None

    if not plan["execution_allowed"]:
        files["stdout"].write_text("", encoding="utf-8")
        files["stderr"].write_text("blocked by RP6 execution plan\n", encoding="utf-8")
        if shell_approval and shell_approval_request_id:
            _append_approval_transcript(files["approval_events"], shell_approval, target or "process", shell_approval_request_id, "deny")
        append_jsonl(
            files["process_events"],
            _process_event_row(
                command,
                target,
                "blocked",
                started_at,
                plan,
                shell_approval,
                shell_approval_request_id,
                {"decision_reasons": plan["decision_reasons"]},
            ),
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

    if shell_approval and shell_approval_request_id:
        _append_approval_transcript(files["approval_events"], shell_approval, target or "process", shell_approval_request_id, "allow")
    before = snapshot_tree(prepared_run.workspace_path)
    append_jsonl(
        files["process_events"],
        _process_event_row(
            command,
            target,
            "attempted",
            started_at,
            plan,
            shell_approval,
            shell_approval_request_id,
            {
                "command_sha256": plan["command"]["sha256"],
                "cwd": str(prepared_run.workspace_path),
            },
        ),
    )

    exit_code = 0
    outcome = "completed"
    try:
        completed = subprocess.run(
            command,
            cwd=prepared_run.workspace_path,
            env=_policy_env(prepared_run.workspace_path, prepared_run.artifacts_dir, files, plan),
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
    _harden_semantic_events(files["semantic_events"], plan)
    _append_unrecorded_diff_events(prepared_run.workspace_path, before, files, plan["canary_labels"])
    _append_log_canary_hits(files, stdout, stderr, plan["canary_labels"])
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


def _process_event_row(
    command: list[str],
    target: str | None,
    status: str,
    timestamp: str,
    plan: dict[str, Any],
    approval: dict[str, Any] | None,
    approval_request_id: str | None,
    extra: dict[str, Any],
) -> dict[str, Any]:
    row = {
        "argv": command,
        "event": "shell.exec",
        "operation": "exec",
        "status": status,
        "target": target,
        "timestamp": timestamp,
        "matched_rule_ids": plan["matched_rule_ids"],
        "matched_allow_rule": plan["matched_rule_ids"][0] if plan["matched_rule_ids"] else None,
        "allowed_by_contract": bool(plan["matched_rule_ids"]),
    }
    if approval and approval_request_id:
        row["approval_required"] = True
        row["approval_request_id"] = approval_request_id
    row.update(extra)
    return row


def _contract_policy(contract: dict[str, Any], workspace_path: Path, runtime_profile: dict[str, Any]) -> dict[str, Any]:
    filesystem = contract.get("access", {}).get("filesystem", {})
    reads = filesystem.get("reads", {}) if isinstance(filesystem, dict) else {}
    writes = filesystem.get("writes", {}) if isinstance(filesystem, dict) else {}
    disabled_components = _ablation_disabled_components(runtime_profile)
    read_allow = _path_rules(reads.get("allow", []))
    read_deny = _path_rules(reads.get("deny", []))
    write_allow = _path_rules(writes.get("allow", []))
    write_deny = _path_rules(writes.get("deny", []))
    if "filesystem_read_scope" in disabled_components:
        read_allow = [_ablation_path_rule("RP6-ABL-FS-R-ALLOW-ALL", "./**")]
        read_deny = []
    if "filesystem_write_scope" in disabled_components:
        write_allow = [_ablation_path_rule("RP6-ABL-FS-W-ALLOW-ALL", "./**")]
        write_deny = []
    if "persistence_cache_access" in disabled_components:
        write_allow.extend(_persistence_cache_ablation_rules(contract.get("access", {}).get("persistence", {})))
    return {
        "ablation_disabled_components": disabled_components,
        "workspace_root": str(workspace_path.resolve()),
        "read_allow": read_allow,
        "read_deny": read_deny,
        "write_allow": write_allow,
        "write_deny": write_deny,
        "network": contract.get("access", {}).get("network", {}),
        "tools": contract.get("access", {}).get("tools", {}),
        "persistence": contract.get("access", {}).get("persistence", {}),
        "approval_required": contract.get("approval_required", []) or [],
        "canary_labels": extract_canary_labels(contract),
    }


def _path_rules(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for rule in rules or []:
        match = rule.get("match", {})
        path_glob = match.get("path_glob") or match.get("destination_glob")
        if not isinstance(path_glob, str):
            continue
        normalized.append({"id": rule.get("id"), "path_glob": _normalize_path(path_glob), "rule": rule})
    return normalized


def _ablation_path_rule(rule_id: str, path_glob: str) -> dict[str, Any]:
    return {
        "id": rule_id,
        "path_glob": _normalize_path(path_glob),
        "rule": {
            "id": rule_id,
            "event_type": "filesystem.access",
            "match": {"path_glob": path_glob},
            "reason": "RP6 component ablation relaxes this path surface for controlled evidence generation.",
        },
    }


def _persistence_cache_ablation_rules(persistence: Any) -> list[dict[str, Any]]:
    if not isinstance(persistence, dict):
        return []
    path_globs: list[str] = []
    for side in ("allow", "deny"):
        for rule in persistence.get(side, []) or []:
            if not isinstance(rule, dict):
                continue
            match = rule.get("match", {})
            if not isinstance(match, dict):
                continue
            path_glob = match.get("path_glob")
            if isinstance(path_glob, str) and path_glob not in path_globs:
                path_globs.append(path_glob)
    return [
        _ablation_path_rule(f"RP6-ABL-PER-W-{index:03d}", path_glob)
        for index, path_glob in enumerate(path_globs, start=1)
    ]


def _ablation_disabled_components(runtime_profile: dict[str, Any]) -> list[str]:
    metadata = runtime_profile.get("metadata", {})
    if not isinstance(metadata, dict):
        return []
    config = metadata.get("rp6_component_ablation", {})
    if not isinstance(config, dict):
        return []
    components = config.get("disabled_components", [])
    if not isinstance(components, list):
        return []
    return sorted(str(component) for component in components)


def _build_execution_plan(
    command: list[str],
    runtime_profile: dict[str, Any],
    contract: dict[str, Any],
    workspace_path: Path,
    task_prompt: str,
    policy: dict[str, Any],
) -> dict[str, Any]:
    profile_allowed, profile_reasons = _profile_command_decision(command, runtime_profile)
    adapter_allowed, adapter_reasons = _adapter_command_decision(command)
    contract_allowed, contract_reasons, rule_ids = _contract_command_decision(command, contract)
    execution_allowed = bool(command) and profile_allowed and adapter_allowed and contract_allowed
    timeout_seconds = runtime_profile["features"]["shell"]["timeout_seconds"]
    env_allowlist = runtime_profile["features"]["credentials"].get("env_allowlist", [])
    return {
        "schema_version": "0.1",
        "profile_id": runtime_profile["profile_id"],
        "command": {
            "argv": command,
            "executable": command[0] if command else None,
            "sha256": _hash_json(command),
        },
        "execution_allowed": execution_allowed,
        "decision_reasons": profile_reasons + adapter_reasons + contract_reasons,
        "matched_rule_ids": rule_ids,
        "workspace_path": str(workspace_path),
        "task_prompt_hash": _hash_text(task_prompt),
        "timeout_seconds": timeout_seconds,
        "env_manifest": {
            "env_allowlist": env_allowlist,
            "host_env_forwarded": [name for name in env_allowlist if name == "PATH"],
            "home_is_run_workspace": True,
            "synthetic_credentials": ["CANARY_API_KEY"] if "CANARY_API_KEY" in env_allowlist else [],
        },
        "policy": policy,
        "ablation_disabled_components": policy["ablation_disabled_components"],
        "canary_labels": policy["canary_labels"],
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


def _adapter_command_decision(command: list[str]) -> tuple[bool, list[str]]:
    if not command:
        return False, ["no command provided"]
    if Path(command[0]).name not in {"python3", "python"}:
        return False, ["RP6 adapter supports controlled Python commands only"]
    return True, ["RP6 adapter supports controlled Python command"]


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


def _policy_env(
    workspace_path: Path,
    artifacts_dir: Path,
    files: dict[str, Path],
    plan: dict[str, Any],
) -> dict[str, str]:
    workspace_abs = workspace_path.resolve()
    env: dict[str, str] = {
        "HOME": str(workspace_abs),
        "PYTHONDONTWRITEBYTECODE": "1",
        "SKILLDIFF_REPO_ROOT": str(workspace_abs),
        "SKILLDIFF_OUTPUT_ROOT": str(workspace_abs),
        "SKILLDIFF_RUNTIME_PROFILE": plan["profile_id"],
        "SKILLDIFF_SEMANTIC_EVENTS": str(files["semantic_events"].resolve()),
        "SKILLDIFF_FAKE_SINK_URL": "http://sink.rp6.invalid/skilldiff-fake-sink",
    }
    if "PATH" in plan["env_manifest"]["env_allowlist"]:
        env["PATH"] = os.environ.get("PATH", "")
    if "CANARY_API_KEY" in plan["env_manifest"]["env_allowlist"]:
        env["CANARY_API_KEY"] = "synthetic-rp6-credential"

    policy_path = (artifacts_dir / "rp6_policy.json").resolve()
    write_json(
        policy_path,
        {
            "policy": plan["policy"],
            "file_read_events": str(files["file_read_events"].resolve()),
            "file_write_events": str(files["file_write_events"].resolve()),
            "file_observations": str(files["file_observations"].resolve()),
            "approval_events": str(files["approval_events"].resolve()),
            "network_events": str(files["network_events"].resolve()),
            "network_sink_requests": str(files["network_sink_requests"].resolve()),
        },
    )
    shim_dir = _install_policy_shim(artifacts_dir / "rp6_policy_shim").resolve()
    env["PYTHONPATH"] = _prepend_path_env(str(shim_dir), env.get("PYTHONPATH", ""))
    env["SKILLDIFF_RP6_POLICY_PATH"] = str(policy_path)
    return env


def _install_policy_shim(shim_dir: Path) -> Path:
    shim_dir.mkdir(parents=True, exist_ok=True)
    (shim_dir / "sitecustomize.py").write_text(_PYTHON_POLICY_SHIM, encoding="utf-8")
    return shim_dir


def _prepend_path_env(value: str, existing: str) -> str:
    if not existing:
        return value
    return value + os.pathsep + existing


def _append_unrecorded_diff_events(
    workspace_path: Path,
    before: dict[str, dict[str, Any]],
    files: dict[str, Path],
    canary_labels: list[str],
) -> None:
    after = snapshot_tree(workspace_path)
    observed_paths = _observed_write_paths(files["file_observations"])
    for row in diff_snapshots(before, after):
        rel = _normalize_path(row["path"])
        if rel in observed_paths:
            continue
        path = workspace_path / rel.removeprefix("./")
        labels: list[str] = []
        if path.exists() and path.is_file():
            labels = scan_text_for_canaries(path.read_text(encoding="utf-8", errors="replace"), canary_labels)
        observation = dict(row)
        observation["path"] = rel
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
                    "path": rel,
                    "sink_type": "local_file",
                    "timestamp": utc_now(),
                },
            )


def _observed_write_paths(path: Path) -> set[str]:
    paths: set[str] = set()
    if not path.exists():
        return paths
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("event") in {"filesystem.write", "filesystem.modify"} and isinstance(row.get("path"), str):
                paths.add(_normalize_path(row["path"]))
    return paths


def _append_log_canary_hits(files: dict[str, Path], stdout: str, stderr: str, canary_labels: list[str]) -> None:
    for sink_type, content, path in (
        ("stdout_log", stdout, files["stdout"]),
        ("stderr_log", stderr, files["stderr"]),
    ):
        labels = scan_text_for_canaries(content, canary_labels)
        if labels:
            append_jsonl(
                files["canary_hits"],
                {
                    "event": "canary.observe",
                    "labels": labels,
                    "path": str(path),
                    "sink_type": sink_type,
                    "timestamp": utc_now(),
                },
            )


def _harden_semantic_events(path: Path, plan: dict[str, Any]) -> None:
    if not path.exists():
        return
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    policy = plan["policy"]
    disabled_components = set(policy.get("ablation_disabled_components", []))
    hardened = []
    for row in rows:
        event_type = row.get("event")
        if event_type == "tool.call":
            if "semantic_tool_policy" in disabled_components:
                hardened.append(row)
                continue
            decision = _resolve_rule_bag(policy.get("tools", {}), row, "tool")
            if decision:
                _apply_semantic_decision(row, decision)
        elif event_type == "persistence.write":
            if "persistence_cache_access" in disabled_components:
                hardened.append(row)
                continue
            decision = _resolve_rule_bag(policy.get("persistence", {}), row, "persistence")
            if decision:
                _apply_semantic_decision(row, decision)
        hardened.append(row)
    write_jsonl(path, hardened)


def _resolve_rule_bag(bag: dict[str, Any], row: dict[str, Any], row_kind: str) -> dict[str, Any] | None:
    matched: list[tuple[str, tuple[int, int], dict[str, Any]]] = []
    for side in ("allow", "deny"):
        for rule in bag.get(side, []) or []:
            if rule.get("event_type") != row.get("event"):
                continue
            if _semantic_rule_matches(rule.get("match", {}), row, row_kind):
                matched.append((side, _rule_specificity(rule.get("match", {})), rule))
    if not matched:
        return None
    best_score = max(score for _side, score, _rule in matched)
    best = [item for item in matched if item[1] == best_score]
    deny = next((rule for side, _score, rule in best if side == "deny"), None)
    if deny:
        return {"side": "deny", "rule": deny}
    return {"side": "allow", "rule": best[0][2]}


def _semantic_rule_matches(match: dict[str, Any], row: dict[str, Any], row_kind: str) -> bool:
    metadata = row.get("metadata", {}) if isinstance(row.get("metadata"), dict) else {}
    if "tool_name" in match and (metadata.get("tool_name") or row.get("target")) != match["tool_name"]:
        return False
    if "mutation" in match and bool(metadata.get("mutation")) != bool(match["mutation"]):
        return False
    if "store_type" in match and metadata.get("store_type") != match["store_type"]:
        return False
    if "retention_scope" in match and metadata.get("retention_scope") != match["retention_scope"]:
        return False
    if "post_cleanup_allowed" in match and bool(metadata.get("post_cleanup_allowed")) != bool(match["post_cleanup_allowed"]):
        return False
    if "path_glob" in match:
        target = row.get("target")
        if not isinstance(target, str) or not _match_path_glob(match["path_glob"], target):
            return False
    if "sink_type" in match and row.get("sink_type") != match["sink_type"]:
        return False
    if "may_contain_canary" in match and bool(row.get("canary_labels")) != bool(match["may_contain_canary"]):
        return False
    return row_kind in {"tool", "persistence"}


def _apply_semantic_decision(row: dict[str, Any], decision: dict[str, Any]) -> None:
    rule = decision["rule"]
    rule_id = rule.get("id")
    if decision["side"] == "deny":
        row["status"] = "blocked"
        row["enforcement_outcome"] = "blocked"
        row["allowed_by_contract"] = False
        row["matched_deny_rule"] = rule_id
    else:
        row.setdefault("enforcement_outcome", "allowed")
        row["allowed_by_contract"] = True
        row["matched_allow_rule"] = rule_id
    if rule_id:
        row["contract_rule_ids"] = [rule_id]


def _approval_for_shell(plan: dict[str, Any], command: list[str]) -> dict[str, Any] | None:
    if "approval_requirement" in set(plan.get("policy", {}).get("ablation_disabled_components", [])):
        return None
    for approval in plan.get("policy", {}).get("approval_required", []):
        if approval.get("event_type") != "shell.exec":
            continue
        if _command_rule_matches(approval.get("match", {}), command):
            return approval
    return None


def _append_approval_transcript(path: Path, approval: dict[str, Any], target: str, request_id: str, decision: str) -> None:
    risk_label = "contract_required_action"
    for event, status, operation in (
        ("approval.required", "observed", "require"),
        ("approval.prompt", "observed", "prompt"),
        ("approval.decision", "succeeded", decision),
    ):
        append_jsonl(
            path,
            {
                "event": event,
                "status": status,
                "target": target,
                "operation": operation,
                "approval_request_id": request_id,
                "enforcement_outcome": "allowed" if decision == "allow" and event == "approval.decision" else "observed",
                "timestamp": utc_now(),
                "risk_label": risk_label,
                "decision": decision if event == "approval.decision" else None,
                "approval_rule_id": approval.get("id"),
            },
        )


def _approval_request_id(approval: dict[str, Any], event_type: str, target: str) -> str:
    source = f"{approval.get('id', 'approval')}:{event_type}:{target}"
    return "apr-" + hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]


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
            if not isinstance(rel_path, str) or rel_path.startswith("./.skilldiff"):
                continue
            output_path = workspace_path / rel_path.removeprefix("./")
            if not output_path.exists() or not output_path.is_file():
                continue
            outputs.append({"path": _normalize_path(rel_path), "size": output_path.stat().st_size})
    return outputs


def _matches_any_path_rule(path: str, rules: list[dict[str, Any]]) -> bool:
    return any(_match_path_glob(rule["path_glob"], path) for rule in rules)


def _match_path_glob(pattern: str, observed_path: str) -> bool:
    return fnmatch.fnmatchcase(_normalize_path(observed_path), _normalize_path(pattern))


def _normalize_path(path: str) -> str:
    if path.startswith(("env:", "cred:", "~/", "/")):
        return path
    if not path.startswith("./"):
        path = "./" + path
    parts = []
    for part in path[2:].split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "./" + "/".join(parts)


def _rule_specificity(rule_match: dict[str, Any]) -> tuple[int, int]:
    if "argv_exact" in rule_match:
        return (90, len(rule_match["argv_exact"]))
    if "argv_prefix" in rule_match:
        return (80, len(rule_match["argv_prefix"]))
    if "executable" in rule_match:
        value = rule_match["executable"]
        return (10 if value == "*" else 70, len(value))
    if "path_glob" in rule_match:
        value = _normalize_path(rule_match["path_glob"])
        return (40 if "**" in value else 60 if "*" in value else 90, len(value))
    if "destination_glob" in rule_match:
        value = _normalize_path(rule_match["destination_glob"])
        return (75, len(value))
    if "sink_type" in rule_match and rule_match.get("may_contain_canary"):
        return (95, len(rule_match["sink_type"]))
    if "tool_name" in rule_match:
        return (85, len(rule_match["tool_name"]))
    if "store_type" in rule_match:
        return (65, len(rule_match["store_type"]))
    if "domain_glob" in rule_match:
        value = rule_match["domain_glob"]
        return (10 if value == "*" else 70, len(value))
    if "domain" in rule_match:
        return (90, len(rule_match["domain"]))
    return (1, 0)


def _hash_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hash_json(value: Any) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


_PYTHON_POLICY_SHIM = textwrap.dedent(
    r'''
    from __future__ import annotations

    import builtins
    import errno
    import fnmatch
    import hashlib
    import json
    import os
    import pathlib
    import socket
    import threading
    import urllib.error
    import urllib.parse
    import urllib.request
    from datetime import datetime, timezone

    _POLICY_PATH = os.environ.get("SKILLDIFF_RP6_POLICY_PATH")
    _CONFIG = json.loads(pathlib.Path(_POLICY_PATH).read_text(encoding="utf-8")) if _POLICY_PATH else {}
    _POLICY = _CONFIG.get("policy", {})
    _DISABLED_COMPONENTS = set(_POLICY.get("ablation_disabled_components") or [])
    _ROOT = pathlib.Path(_POLICY.get("workspace_root", os.getcwd())).resolve()
    _LOCK = threading.Lock()
    _ORIGINAL_OPEN = builtins.open
    _ORIGINAL_PATH_OPEN = pathlib.Path.open
    _ORIGINAL_URLOPEN = urllib.request.urlopen
    _ORIGINAL_SOCKET_CONNECT = socket.socket.connect
    _ORIGINAL_SOCKET_CONNECT_EX = socket.socket.connect_ex
    _ORIGINAL_SOCKET_SEND = socket.socket.send
    _ORIGINAL_SOCKET_SENDALL = socket.socket.sendall
    _ORIGINAL_CREATE_CONNECTION = socket.create_connection
    _SOCKET_TARGETS = {}

    def _utc_now():
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def _append_jsonl(path, row):
        if not path:
            return
        with _ORIGINAL_OPEN(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    def _normalize(path):
        if path.startswith(("env:", "cred:", "~/", "/")):
            return path
        if not path.startswith("./"):
            path = "./" + path
        parts = []
        for part in path[2:].split("/"):
            if part in {"", "."}:
                continue
            if part == "..":
                if parts:
                    parts.pop()
                continue
            parts.append(part)
        return "./" + "/".join(parts)

    def _rel(path):
        try:
            candidate = pathlib.Path(os.fspath(path))
        except TypeError:
            candidate = pathlib.Path(str(path))
        if not candidate.is_absolute():
            candidate = pathlib.Path(os.getcwd()) / candidate
        try:
            resolved = candidate.resolve(strict=False)
            rel = resolved.relative_to(_ROOT)
        except ValueError:
            return None
        return "./" + rel.as_posix()

    def _specificity(glob):
        normalized = _normalize(glob)
        return (40 if "**" in normalized else 60 if "*" in normalized else 90, len(normalized))

    def _matches(rule, rel):
        return fnmatch.fnmatchcase(_normalize(rel), _normalize(rule["path_glob"]))

    def _component_disabled(component):
        return component in _DISABLED_COMPONENTS

    def _decision(rel, side):
        allow = [rule for rule in _POLICY.get(side + "_allow", []) if _matches(rule, rel)]
        deny = [rule for rule in _POLICY.get(side + "_deny", []) if _matches(rule, rel)]
        matched = [("allow", _specificity(rule["path_glob"]), rule) for rule in allow]
        matched.extend(("deny", _specificity(rule["path_glob"]), rule) for rule in deny)
        if not matched:
            return {"allowed": False, "rule": None, "side": "deny", "reason": "default_deny"}
        best_score = max(score for _side, score, _rule in matched)
        best = [item for item in matched if item[1] == best_score]
        deny_rule = next((rule for item_side, _score, rule in best if item_side == "deny"), None)
        if deny_rule is not None:
            return {"allowed": False, "rule": deny_rule, "side": "deny", "reason": "matched_deny"}
        return {"allowed": True, "rule": best[0][2], "side": "allow", "reason": "matched_allow"}

    def _approval_for(event_type, rel):
        if _component_disabled("approval_requirement"):
            return None
        for approval in _POLICY.get("approval_required", []):
            if approval.get("event_type") != event_type:
                continue
            match = approval.get("match", {})
            glob = match.get("path_glob") or match.get("destination_glob")
            if glob and fnmatch.fnmatchcase(_normalize(rel), _normalize(glob)):
                return approval
        return None

    def _request_id(approval, event_type, rel):
        source = f"{approval.get('id', 'approval')}:{event_type}:{rel}"
        return "apr-" + hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]

    def _append_approval(approval, rel, request_id, decision):
        for event, status, operation in (
            ("approval.required", "observed", "require"),
            ("approval.prompt", "observed", "prompt"),
            ("approval.decision", "succeeded", decision),
        ):
            _append_jsonl(
                _CONFIG.get("approval_events"),
                {
                    "event": event,
                    "status": status,
                    "target": rel,
                    "operation": operation,
                    "approval_request_id": request_id,
                    "enforcement_outcome": "allowed" if event == "approval.decision" and decision == "allow" else "observed",
                    "timestamp": _utc_now(),
                    "risk_label": "contract_required_action",
                    "decision": decision if event == "approval.decision" else None,
                    "approval_rule_id": approval.get("id"),
                },
            )

    def _row(event, rel, mode, status, decision, error=None, approval=None, request_id=None):
        rule = decision.get("rule")
        row = {
            "event": event,
            "instrumentation_model": "rp6_python_policy_wrapper",
            "operation": "read" if event == "filesystem.read" else "write",
            "path": rel,
            "status": status,
            "timestamp": _utc_now(),
            "mode": mode,
            "allowed_by_contract": bool(decision.get("allowed")),
            "decision_reason": decision.get("reason"),
            "matched_rule_ids": [rule.get("id")] if rule and rule.get("id") else [],
            "matched_allow_rule": rule.get("id") if rule and decision.get("side") == "allow" else None,
            "matched_deny_rule": rule.get("id") if rule and decision.get("side") == "deny" else None,
        }
        if approval and request_id:
            row["approval_required"] = True
            row["approval_request_id"] = request_id
        if error is not None:
            row["error_type"] = type(error).__name__
            row["error_message"] = str(error)
        return row

    def _is_read_mode(mode):
        mode = mode or "r"
        return "r" in mode and not any(flag in mode for flag in ("w", "a", "x", "+"))

    def _is_write_mode(mode):
        mode = mode or "r"
        return any(flag in mode for flag in ("w", "a", "x", "+"))

    def _record_file(path, mode, event, status, decision, error=None, approval=None, request_id=None):
        rel = _rel(path)
        if rel is None:
            return
        row = _row(event, rel, mode, status, decision, error, approval, request_id)
        with _LOCK:
            if event == "filesystem.read":
                _append_jsonl(_CONFIG.get("file_read_events"), row)
            else:
                _append_jsonl(_CONFIG.get("file_write_events"), row)
                _append_jsonl(_CONFIG.get("file_observations"), row)

    def _guard_open(path, mode):
        rel = _rel(path)
        if rel is None:
            return None, None, None
        if _is_read_mode(mode):
            decision = _decision(rel, "read")
            if not decision["allowed"]:
                error = FileNotFoundError(f"RP6 blocked read: {rel}")
                _record_file(path, mode, "filesystem.read", "blocked", decision, error)
                raise error
            return rel, decision, None
        if _is_write_mode(mode):
            decision = _decision(rel, "write")
            approval = _approval_for("filesystem.write", rel)
            request_id = _request_id(approval, "filesystem.write", rel) if approval else None
            if approval:
                _append_approval(approval, rel, request_id, "allow" if decision["allowed"] else "deny")
            if not decision["allowed"]:
                error = PermissionError(f"RP6 blocked write: {rel}")
                _record_file(path, mode, "filesystem.write", "blocked", decision, error, approval, request_id)
                raise error
            return rel, decision, (approval, request_id)
        return rel, None, None

    def _open(path, mode="r", *args, **kwargs):
        rel, decision, approval_data = _guard_open(path, mode)
        try:
            handle = _ORIGINAL_OPEN(path, mode, *args, **kwargs)
        except Exception as exc:
            if rel and decision:
                event = "filesystem.read" if _is_read_mode(mode) else "filesystem.write"
                approval, request_id = approval_data or (None, None)
                _record_file(path, mode, event, "failed", decision, exc, approval, request_id)
            raise
        if rel and decision:
            event = "filesystem.read" if _is_read_mode(mode) else "filesystem.write"
            approval, request_id = approval_data or (None, None)
            _record_file(path, mode, event, "succeeded", decision, None, approval, request_id)
        return handle

    def _path_open(self, mode="r", buffering=-1, encoding=None, errors=None, newline=None):
        return _open(self, mode, buffering=buffering, encoding=encoding, errors=errors, newline=newline)

    builtins.open = _open
    pathlib.Path.open = _path_open

    class _RP6NetworkBlocked(Exception):
        pass

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

    def _network_row(url, method, data, event, operation, status="blocked", enforcement_outcome="blocked", allowed=False):
        parsed = urllib.parse.urlparse(url)
        payload = _payload_bytes(data)
        labels = []
        text = payload.decode("utf-8", errors="replace") if payload else ""
        for label in _POLICY.get("canary_labels", []):
            if label and label in text:
                labels.append(label)
        return {
            "event": event,
            "instrumentation_model": "rp6_python_network_blocker",
            "operation": operation,
            "url": url,
            "domain": parsed.hostname or "",
            "port": parsed.port,
            "scheme": parsed.scheme,
            "method": method,
            "status": status,
            "enforcement_outcome": enforcement_outcome,
            "sink_type": "fake_http" if (parsed.hostname or "").lower().endswith(".invalid") else "external_http",
            "timestamp": _utc_now(),
            "payload_hash": "sha256:" + hashlib.sha256(payload).hexdigest() if payload else None,
            "payload_size": len(payload),
            "payload_redacted_excerpt": "<redacted>" if payload else "",
            "canary_labels": sorted(set(labels)),
            "public_internet_contacted": False,
            "matched_rule_ids": (
                ["RP6-ABL-NET-ALLOW-ALL"]
                if allowed
                else [rule.get("id") for rule in _POLICY.get("network", {}).get("deny", []) if rule.get("id")]
            ),
            "matched_allow_rule": "RP6-ABL-NET-ALLOW-ALL" if allowed else None,
            "allowed_by_contract": allowed,
        }

    class _RP6AblationResponse:
        status = 204

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self, *args, **kwargs):
            return b""

        def getcode(self):
            return self.status

    def _socket_url(address):
        if isinstance(address, tuple) and len(address) >= 2:
            return f"tcp://{address[0]}:{address[1]}"
        return f"socket://{address}"

    def _remember_socket_target(sock, url):
        _SOCKET_TARGETS[id(sock)] = url

    def _socket_target(sock):
        return _SOCKET_TARGETS.get(id(sock), "socket://unknown")

    def _socket_connect(self, address):
        url = _socket_url(address)
        if _component_disabled("network_egress_blocker"):
            with _LOCK:
                _remember_socket_target(self, url)
                _append_jsonl(_CONFIG.get("network_events"), _network_row(url, "SOCKET", None, "network.connect", "connect", "succeeded", "allowed", True))
            return None
        error = OSError(errno.EACCES, f"RP6 blocked socket connect: {url}")
        with _LOCK:
            _remember_socket_target(self, url)
            _append_jsonl(_CONFIG.get("network_events"), _network_row(url, "SOCKET", None, "network.connect", "connect"))
        raise error

    def _socket_connect_ex(self, address):
        url = _socket_url(address)
        if _component_disabled("network_egress_blocker"):
            with _LOCK:
                _remember_socket_target(self, url)
                _append_jsonl(_CONFIG.get("network_events"), _network_row(url, "SOCKET", None, "network.connect", "connect", "succeeded", "allowed", True))
            return 0
        with _LOCK:
            _remember_socket_target(self, url)
            _append_jsonl(_CONFIG.get("network_events"), _network_row(url, "SOCKET", None, "network.connect", "connect"))
        return errno.EACCES

    def _socket_send(self, data, *args, **kwargs):
        url = _socket_target(self)
        if _component_disabled("network_egress_blocker"):
            with _LOCK:
                _append_jsonl(_CONFIG.get("network_events"), _network_row(url, "SOCKET", data, "network.send", "send", "succeeded", "allowed", True))
            return len(data or b"")
        error = OSError(errno.EACCES, f"RP6 blocked socket send: {url}")
        with _LOCK:
            _append_jsonl(_CONFIG.get("network_events"), _network_row(url, "SOCKET", data, "network.send", "send"))
        raise error

    def _socket_sendall(self, data, *args, **kwargs):
        _socket_send(self, data, *args, **kwargs)

    def _create_connection(address, timeout=None, source_address=None, *args, **kwargs):
        url = _socket_url(address)
        if _component_disabled("network_egress_blocker"):
            raw_socket = socket.socket()
            _remember_socket_target(raw_socket, url)
            with _LOCK:
                _append_jsonl(_CONFIG.get("network_events"), _network_row(url, "SOCKET", None, "network.connect", "connect", "succeeded", "allowed", True))
            return raw_socket
        error = OSError(errno.EACCES, f"RP6 blocked socket create_connection: {url}")
        with _LOCK:
            _append_jsonl(_CONFIG.get("network_events"), _network_row(url, "SOCKET", None, "network.connect", "connect"))
        raise error

    def _urlopen(request, data=None, *args, **kwargs):
        url = _request_url(request)
        method = _request_method(request, data)
        body = _request_data(request, data)
        if _component_disabled("network_egress_blocker"):
            with _LOCK:
                _append_jsonl(_CONFIG.get("network_events"), _network_row(url, method, None, "network.connect", "connect", "succeeded", "allowed", True))
                if body is not None:
                    _append_jsonl(_CONFIG.get("network_events"), _network_row(url, method, body, "network.send", "send", "succeeded", "allowed", True))
            return _RP6AblationResponse()
        error = _RP6NetworkBlocked(f"RP6 blocked network access: {url}")
        with _LOCK:
            _append_jsonl(_CONFIG.get("network_events"), _network_row(url, method, None, "network.connect", "connect"))
            if body is not None:
                _append_jsonl(_CONFIG.get("network_events"), _network_row(url, method, body, "network.send", "send"))
        raise urllib.error.URLError(error)

    urllib.request.urlopen = _urlopen
    socket.socket.connect = _socket_connect
    socket.socket.connect_ex = _socket_connect_ex
    socket.socket.send = _socket_send
    socket.socket.sendall = _socket_sendall
    socket.create_connection = _create_connection
    '''
).lstrip()
