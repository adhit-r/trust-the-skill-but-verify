"""Deterministic hosted-style simulator for the RP1 restricted profile."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import fnmatch
import hashlib
import json
import shutil

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
from .local import _copy_seed_workspace, _generated_outputs_from_observations
from skilldiff.traces.events import extract_canary_labels


class RestrictedHostedSimAdapter(RuntimeAdapter):
    adapter_id = "restricted_hosted_sim"

    def capability_snapshot(self, runtime_profile: dict[str, Any]) -> dict[str, Any]:
        snapshot = base_capability_snapshot(runtime_profile, self.adapter_id)
        snapshot["simulation_boundary"] = {
            "provider_claim": "none",
            "runtime_claim": "hosted_style_projection_only",
            "execution_model": "deterministic_report_writer_simulator",
            "unsupported_surfaces": ["shell", "network", "persistence"],
            "input_projection": "workspace files are modeled as uploaded inputs via metadata and upload mirror",
            "output_scope": "./outputs/** only",
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
        if run_dir.exists():
            shutil.rmtree(run_dir)
        workspace_path = run_dir / "workspace"
        copied_files = _copy_seed_workspace(workspace_seed, workspace_path)
        upload_projection_path = workspace_path / "uploads"
        upload_projection_files = _copy_seed_workspace(workspace_seed, upload_projection_path)
        (workspace_path / "outputs").mkdir(parents=True, exist_ok=True)
        files = ensure_artifact_files(run_dir)
        execution_plan = _build_execution_plan(command, runtime_profile, contract, workspace_path, task_prompt)

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
                "upload_projection_file_count": upload_projection_files,
                "workspace_mode": "mirrored_seed_workspace_with_upload_projection",
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
                        "mode": "simulated_hosted_projection",
                    }
                ]
            },
        )
        write_json(
            files["instrumentation_status"],
            {
                "adapter_id": self.adapter_id,
                "file_read_provenance": "rp1_upload_projection_wrapper",
                "file_write_provenance": "rp1_report_writer_projection",
                "network_provenance": "rp1_network_surface_disabled",
                "process_provenance": "rp1_shell_surface_disabled",
                "tool_provenance": "rp1_semantic_report_writer_fixture",
                "trace_valid": True,
                "warnings": [
                    "RP1 is a deterministic hosted-style simulator, not a commercial hosted runtime execution",
                    "shell, network, and persistence events are simulated capability-boundary records only",
                    "upload-only behavior is represented through projected metadata and upload mirror paths",
                    "generated outputs are local simulation artifacts, not defense-success evidence",
                ],
            },
        )
        _write_empty_artifacts(files)
        write_jsonl(
            files["file_observations"],
            [
                {
                    "copied_file_count": copied_files,
                    "event": "workspace_seed_copied",
                    "path": str(workspace_seed),
                    "profile_id": runtime_profile["profile_id"],
                    "timestamp": utc_now(),
                },
                {
                    "event": "upload_projection_created",
                    "path": str(upload_projection_path),
                    "profile_id": runtime_profile["profile_id"],
                    "projected_file_count": upload_projection_files,
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
            workspace_path=workspace_path,
            artifacts_dir=run_dir,
            run_metadata_path=files["run_metadata"],
            capabilities_path=files["capabilities"],
            approval_plan_path=files["approvals"],
            invocation=command if command else ["report_writer", "simulation"],
            dry_run=run_spec.dry_run,
        )

    def run(self, prepared_run: PreparedRun) -> RunExecution:
        files = ensure_artifact_files(prepared_run.artifacts_dir)
        plan = json.loads(files["execution_plan"].read_text(encoding="utf-8"))
        started_at = utc_now()

        if prepared_run.dry_run:
            files["stdout"].write_text("restricted hosted simulator dry run\n", encoding="utf-8")
            files["stderr"].write_text("", encoding="utf-8")
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

        read_count = _record_simulated_reads(files["file_read_events"], plan)
        output_summary = _record_simulated_outputs(
            prepared_run.workspace_path,
            files["approval_events"],
            files["semantic_events"],
            files["file_observations"],
            files["file_write_events"],
            plan,
        )
        _record_shell_boundary(files["process_events"], files["approval_events"], plan)
        _record_network_boundary(files["network_attempts"], plan)
        _record_persistence_boundary(files["semantic_events"], plan)
        _record_activation(files["semantic_events"], plan)

        stdout = (
            "restricted hosted simulator completed\n"
            f"simulated_reads={read_count}\n"
            f"generated_outputs={output_summary['generated']}\n"
            f"blocked_outputs={output_summary['blocked']}\n"
            "unsupported_surfaces=shell,network,persistence\n"
        )
        files["stdout"].write_text(stdout, encoding="utf-8")
        files["stderr"].write_text("", encoding="utf-8")
        ended_at = utc_now()
        append_jsonl(
            files["adapter_events"],
            {
                "adapter_id": self.adapter_id,
                "event": "run",
                "mode": "live",
                "outcome": "simulated_completed",
                "timestamp": ended_at,
                "generated_outputs": output_summary["generated"],
                "blocked_outputs": output_summary["blocked"],
                "simulated_reads": read_count,
            },
        )
        return RunExecution(
            adapter_outcome="simulated_completed",
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
                "mode": "dry_run" if prepared_run.dry_run else "simulated_live",
                "run_id": prepared_run.run_id,
                "simulation_only": True,
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
                files["semantic_events"],
                files["canary_hits"],
            ],
            canary_observations=[],
            approval_transcript_path=files["approvals"],
        )

    def cleanup(self, prepared_run: PreparedRun, run_execution: RunExecution) -> CleanupResult:
        files = ensure_artifact_files(prepared_run.artifacts_dir)
        removed_paths = _cleanup_tmp_outputs(prepared_run.workspace_path / "outputs" / "tmp")
        result = CleanupResult(
            status="simulated_ephemeral_state_recorded",
            removed_paths=removed_paths,
            leftover_paths=[prepared_run.artifacts_dir],
            cleanup_path=files["cleanup"],
        )
        write_json(
            files["cleanup"],
            {
                "leftover_paths": [str(path) for path in result.leftover_paths],
                "removed_paths": [str(path) for path in result.removed_paths],
                "run_id": prepared_run.run_id,
                "simulation_only": True,
                "status": result.status,
                "timestamp": utc_now(),
            },
        )
        return result


def _build_execution_plan(
    command: list[str],
    runtime_profile: dict[str, Any],
    contract: dict[str, Any],
    workspace_path: Path,
    task_prompt: str,
) -> dict[str, Any]:
    canary_labels = extract_canary_labels(contract)
    read_plans = _plan_read_events(workspace_path, contract)
    output_plans = _plan_output_events(contract)
    shell_plan = _plan_shell_boundary(command, contract)
    network_plan = _plan_network_boundary(runtime_profile, contract)
    persistence_plan = _plan_persistence_boundary(contract)
    return {
        "schema_version": "0.1",
        "profile_id": runtime_profile["profile_id"],
        "command": {
            "argv": command,
            "executable": command[0] if command else None,
            "sha256": _hash_json(command),
        },
        "task_prompt_hash": _hash_text(task_prompt),
        "task_intent": str(contract.get("task", {}).get("intent", "")),
        "skill_id": contract.get("skill_id"),
        "task_id": contract.get("task_id"),
        "canary_labels": canary_labels,
        "simulated_reads": read_plans,
        "simulated_outputs": output_plans,
        "shell_boundary": shell_plan,
        "network_boundary": network_plan,
        "persistence_boundary": persistence_plan,
        "env_manifest": {
            "env_allowlist": [],
            "host_env_forwarded": [],
            "ambient_credentials_forwarded": False,
            "home_is_run_workspace": False,
        },
        "approval_policy": runtime_profile["features"]["approvals"],
        "monitors": runtime_profile["features"]["instrumentation"],
    }


def _plan_read_events(workspace_path: Path, contract: dict[str, Any]) -> list[dict[str, Any]]:
    rules = contract.get("access", {}).get("filesystem", {}).get("reads", {}).get("allow", [])
    plans: list[dict[str, Any]] = []
    for path in sorted(workspace_path.rglob("*")):
        if not path.is_file():
            continue
        rel = _normalize_path(path.relative_to(workspace_path).as_posix())
        if rel.startswith("./outputs/") or rel.startswith("./uploads/"):
            continue
        rule = _first_matching_rule(rules, rel)
        if rule is None:
            continue
        plans.append(
            {
                "path": rel,
                "upload_projection_path": "./uploads/" + rel.removeprefix("./"),
                "size": path.stat().st_size,
                "sha256": _hash_file(path),
                "matched_allow_rule": rule.get("id"),
                "matched_rule_ids": [rule.get("id")] if rule.get("id") else [],
                "allowed_by_contract": True,
                "canary_labels": [],
            }
        )
    return plans


def _plan_output_events(contract: dict[str, Any]) -> list[dict[str, Any]]:
    allow_rules = contract.get("access", {}).get("filesystem", {}).get("writes", {}).get("allow", [])
    deny_rules = contract.get("access", {}).get("filesystem", {}).get("writes", {}).get("deny", [])
    approval_rules = contract.get("approval_required", [])
    plans: list[dict[str, Any]] = []
    for expected in contract.get("expected_outputs", []):
        target = expected.get("target")
        if not isinstance(target, str) or target.startswith(("~", "/")):
            continue
        normalized_target = _normalize_path(target)
        decision = _path_policy_decision(normalized_target, allow_rules, deny_rules)
        allow_rule = decision["allow_rule"]
        deny_rule = decision["deny_rule"]
        approval_rule = _first_matching_approval(approval_rules, "filesystem.write", normalized_target)
        feasible = normalized_target.startswith("./outputs/") and decision["allowed"]
        reason = "allowed_output_scope" if feasible else "outside_rp1_output_scope_or_contract_allowlist"
        oracle = expected.get("oracle") if isinstance(expected.get("oracle"), dict) else {}
        tokens = [token for token in oracle.get("contains_any", []) if isinstance(token, str)]
        plans.append(
            {
                "expected_output_id": expected.get("id"),
                "target": normalized_target,
                "feasible": feasible,
                "reason": reason,
                "matched_allow_rule": allow_rule.get("id") if allow_rule else None,
                "matched_deny_rule": deny_rule.get("id") if deny_rule else "RP1-OUTPUTS-ONLY",
                "matched_rule_ids": [allow_rule.get("id")] if allow_rule and allow_rule.get("id") else [],
                "approval_rule_id": approval_rule.get("id") if approval_rule else None,
                "approval_required": approval_rule is not None,
                "oracle_tokens": tokens,
            }
        )
    return plans


def _plan_shell_boundary(command: list[str], contract: dict[str, Any]) -> dict[str, Any]:
    deny_rules = contract.get("access", {}).get("shell", {}).get("deny", [])
    matched_rule = _first_matching_command_rule(deny_rules, command) if command else None
    approval_rule = _first_matching_approval(contract.get("approval_required", []), "shell.exec", command) if command else None
    return {
        "target": command[0] if command else "shell.disabled",
        "argv": command,
        "matched_deny_rule": matched_rule.get("id") if matched_rule else "RP1-SHELL-DISABLED",
        "matched_rule_ids": [matched_rule.get("id")] if matched_rule and matched_rule.get("id") else [],
        "approval_rule_id": approval_rule.get("id") if approval_rule else None,
        "approval_required": approval_rule is not None,
        "reason": "shell execution is intentionally unsupported in RP1 simulator",
    }


def _plan_network_boundary(runtime_profile: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    deny_rules = contract.get("access", {}).get("network", {}).get("deny", [])
    matched_rule = deny_rules[0] if deny_rules else None
    fake_sink_domains = runtime_profile["features"]["network"].get("fake_sink_domains", [])
    return {
        "domain": fake_sink_domains[0] if fake_sink_domains else "sink.rp1.invalid",
        "matched_deny_rule": matched_rule.get("id") if matched_rule else "RP1-NETWORK-DISABLED",
        "matched_rule_ids": [matched_rule.get("id")] if matched_rule and matched_rule.get("id") else [],
        "reason": "network surface is intentionally unsupported in RP1 simulator",
    }


def _plan_persistence_boundary(contract: dict[str, Any]) -> dict[str, Any]:
    deny_rules = contract.get("access", {}).get("persistence", {}).get("deny", [])
    matched_rule = deny_rules[0] if deny_rules else None
    return {
        "target": "./outputs/tmp/persistent-state.json",
        "matched_deny_rule": matched_rule.get("id") if matched_rule else "RP1-PERSISTENCE-DISABLED",
        "matched_rule_ids": [matched_rule.get("id")] if matched_rule and matched_rule.get("id") else [],
        "reason": "persistent state is intentionally unsupported in RP1 simulator",
    }


def _record_simulated_reads(path: Path, plan: dict[str, Any]) -> int:
    count = 0
    for read_plan in plan["simulated_reads"]:
        row = {
            "event": "filesystem.read",
            "operation": "read",
            "path": read_plan["path"],
            "status": "observed",
            "timestamp": utc_now(),
            "allowed_by_contract": read_plan["allowed_by_contract"],
            "matched_rule_ids": read_plan["matched_rule_ids"],
            "matched_allow_rule": read_plan["matched_allow_rule"],
            "canary_labels": read_plan["canary_labels"],
            "upload_projection_path": read_plan["upload_projection_path"],
            "size": read_plan["size"],
            "sha256": read_plan["sha256"],
            "simulation_only": True,
        }
        append_jsonl(path, row)
        count += 1
    return count


def _record_simulated_outputs(
    workspace_path: Path,
    approval_events_path: Path,
    semantic_events_path: Path,
    file_observations_path: Path,
    file_write_events_path: Path,
    plan: dict[str, Any],
) -> dict[str, int]:
    generated = 0
    blocked = 0
    for output_plan in plan["simulated_outputs"]:
        request_id = _approval_request_id("filesystem.write", output_plan["target"])
        if output_plan["approval_required"]:
            _append_approval_transcript(
                approval_events_path,
                target=output_plan["target"],
                request_id=request_id,
                decision="allow" if output_plan["feasible"] else "deny",
                approval_rule_id=output_plan["approval_rule_id"],
                reason="deterministic_rp1_report_writer_gate",
            )

        if not output_plan["feasible"]:
            blocked += 1
            blocked_row = {
                "event": "filesystem.write",
                "operation": "write",
                "path": output_plan["target"],
                "status": "blocked",
                "timestamp": utc_now(),
                "allowed_by_contract": False,
                "matched_rule_ids": [],
                "matched_allow_rule": None,
                "matched_deny_rule": output_plan["matched_deny_rule"],
                "approval_required": output_plan["approval_required"],
                "approval_request_id": request_id if output_plan["approval_required"] else None,
                "reason": output_plan["reason"],
                "simulation_only": True,
                "expected_output_id": output_plan["expected_output_id"],
            }
            append_jsonl(file_observations_path, blocked_row)
            append_jsonl(file_write_events_path, blocked_row)
            continue

        target_path = workspace_path / output_plan["target"].removeprefix("./")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        content = _render_output_content(output_plan, plan)
        target_path.write_text(content, encoding="utf-8")
        observation = {
            "event": "filesystem.write",
            "operation": "write",
            "path": output_plan["target"],
            "status": "succeeded",
            "timestamp": utc_now(),
            "allowed_by_contract": True,
            "matched_rule_ids": output_plan["matched_rule_ids"],
            "matched_allow_rule": output_plan["matched_allow_rule"],
            "approval_required": output_plan["approval_required"],
            "approval_request_id": request_id if output_plan["approval_required"] else None,
            "expected_output_id": output_plan["expected_output_id"],
            "sha256": _hash_file(target_path),
            "size": target_path.stat().st_size,
            "simulation_only": True,
        }
        append_jsonl(file_observations_path, observation)
        append_jsonl(file_write_events_path, observation)
        append_jsonl(
            semantic_events_path,
            {
                "event": "tool.call",
                "event_phase": "run",
                "status": "succeeded",
                "target": "report_writer",
                "operation": "write",
                "target_kind": "tool",
                "approval_required": output_plan["approval_required"],
                "approval_request_id": request_id if output_plan["approval_required"] else None,
                "enforcement_outcome": "allowed",
                "payload_redacted": True,
                "metadata": {
                    "expected_output_id": output_plan["expected_output_id"],
                    "output_target": output_plan["target"],
                    "simulation_only": True,
                },
                "timestamp": utc_now(),
            },
        )
        generated += 1
    return {"generated": generated, "blocked": blocked}


def _record_shell_boundary(process_events_path: Path, approval_events_path: Path, plan: dict[str, Any]) -> None:
    shell_plan = plan["shell_boundary"]
    request_id = _approval_request_id("shell.exec", shell_plan["target"])
    if shell_plan["approval_required"]:
        _append_approval_transcript(
            approval_events_path,
            target=shell_plan["target"],
            request_id=request_id,
            decision="deny",
            approval_rule_id=shell_plan["approval_rule_id"],
            reason="rp1_shell_surface_disabled",
        )
    append_jsonl(
        process_events_path,
        {
            "argv": shell_plan["argv"],
            "event": "shell.exec",
            "operation": "exec",
            "status": "blocked",
            "target": shell_plan["target"],
            "timestamp": utc_now(),
            "allowed_by_contract": False,
            "matched_rule_ids": shell_plan["matched_rule_ids"],
            "matched_deny_rule": shell_plan["matched_deny_rule"],
            "approval_required": shell_plan["approval_required"],
            "approval_request_id": request_id if shell_plan["approval_required"] else None,
            "reason": shell_plan["reason"],
            "simulation_only": True,
        },
    )


def _record_network_boundary(network_attempts_path: Path, plan: dict[str, Any]) -> None:
    network_plan = plan["network_boundary"]
    append_jsonl(
        network_attempts_path,
        {
            "event": "network.connect",
            "status": "blocked",
            "domain": network_plan["domain"],
            "operation": "connect",
            "timestamp": utc_now(),
            "allowed_by_contract": False,
            "matched_rule_ids": network_plan["matched_rule_ids"],
            "matched_deny_rule": network_plan["matched_deny_rule"],
            "enforcement_outcome": "blocked",
            "public_internet_contacted": False,
            "simulation_only": True,
            "reason": network_plan["reason"],
        },
    )


def _record_persistence_boundary(semantic_events_path: Path, plan: dict[str, Any]) -> None:
    persistence_plan = plan["persistence_boundary"]
    append_jsonl(
        semantic_events_path,
        {
            "event": "persistence.observe",
            "event_phase": "run",
            "status": "blocked",
            "target": persistence_plan["target"],
            "operation": "write",
            "target_kind": "persistence",
            "enforcement_outcome": "blocked",
            "payload_redacted": True,
            "metadata": {
                "matched_deny_rule": persistence_plan["matched_deny_rule"],
                "matched_rule_ids": persistence_plan["matched_rule_ids"],
                "reason": persistence_plan["reason"],
                "simulation_only": True,
            },
            "timestamp": utc_now(),
        },
    )


def _record_activation(semantic_events_path: Path, plan: dict[str, Any]) -> None:
    target = plan.get("skill_id") or "unknown-skill"
    append_jsonl(
        semantic_events_path,
        {
            "event": "activation.discover",
            "event_phase": "prepare",
            "status": "observed",
            "target": target,
            "operation": "discover",
            "target_kind": "activation",
            "enforcement_outcome": "observed",
            "metadata": {
                "discovery_mode": "manifest_only",
                "simulation_only": True,
                "task_id": plan.get("task_id"),
            },
            "timestamp": utc_now(),
        },
    )
    append_jsonl(
        semantic_events_path,
        {
            "event": "activation.select",
            "event_phase": "prepare",
            "status": "succeeded",
            "target": target,
            "operation": "select",
            "target_kind": "activation",
            "enforcement_outcome": "allowed",
            "metadata": {
                "source_type": "task_prompt",
                "task_intent": plan.get("task_intent"),
                "simulation_only": True,
            },
            "timestamp": utc_now(),
        },
    )


def _cleanup_tmp_outputs(path: Path) -> list[Path]:
    removed: list[Path] = []
    if not path.exists():
        return removed
    for child in sorted(path.rglob("*"), reverse=True):
        if child.is_file():
            child.unlink()
            removed.append(child)
        elif child.is_dir():
            child.rmdir()
            removed.append(child)
    path.rmdir()
    removed.append(path)
    return removed


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


def _first_matching_rule(rules: list[dict[str, Any]], target: str) -> dict[str, Any] | None:
    matches = []
    for rule in rules:
        match = rule.get("match", {})
        path_glob = match.get("path_glob") or match.get("destination_glob")
        if not isinstance(path_glob, str):
            continue
        if fnmatch.fnmatchcase(_normalize_path(target), _normalize_path(path_glob)):
            matches.append((path_glob.count("*"), -len(path_glob), rule))
    if not matches:
        return None
    return sorted(matches, key=lambda item: (item[0], item[1]))[0][2]


def _path_policy_decision(
    target: str,
    allow_rules: list[dict[str, Any]],
    deny_rules: list[dict[str, Any]],
) -> dict[str, Any]:
    matches: list[tuple[int, int, str, dict[str, Any]]] = []
    for side, rules in (("allow", allow_rules), ("deny", deny_rules)):
        for rule in rules:
            match = rule.get("match", {})
            path_glob = match.get("path_glob") or match.get("destination_glob")
            if not isinstance(path_glob, str):
                continue
            if fnmatch.fnmatchcase(_normalize_path(target), _normalize_path(path_glob)):
                score = _path_rule_score(path_glob)
                matches.append((score[0], score[1], side, rule))
    if not matches:
        return {"allowed": False, "allow_rule": None, "deny_rule": None}

    best_specificity = max((wildcard_penalty, length) for wildcard_penalty, length, _side, _rule in matches)
    best = [item for item in matches if (item[0], item[1]) == best_specificity]
    deny_rule = next((rule for _penalty, _length, side, rule in best if side == "deny"), None)
    if deny_rule is not None:
        return {"allowed": False, "allow_rule": None, "deny_rule": deny_rule}
    allow_rule = next(rule for _penalty, _length, side, rule in best if side == "allow")
    return {"allowed": True, "allow_rule": allow_rule, "deny_rule": None}


def _path_rule_score(path_glob: str) -> tuple[int, int]:
    normalized = _normalize_path(path_glob)
    wildcard_penalty = -normalized.count("*")
    return (wildcard_penalty, len(normalized))


def _first_matching_command_rule(rules: list[dict[str, Any]], command: list[str]) -> dict[str, Any] | None:
    for rule in rules:
        match = rule.get("match", {})
        if "argv_exact" in match and command == match["argv_exact"]:
            return rule
        if "argv_prefix" in match and command[: len(match["argv_prefix"])] == match["argv_prefix"]:
            return rule
        if "executable" in match and command:
            executable = Path(command[0]).name
            pattern = match["executable"]
            if pattern == "*" or executable == pattern or command[0] == pattern:
                return rule
    return None


def _first_matching_approval(
    rules: list[dict[str, Any]],
    event_type: str,
    target: str | list[str],
) -> dict[str, Any] | None:
    for rule in rules:
        if rule.get("event_type") != event_type:
            continue
        match = rule.get("match", {})
        if isinstance(target, list):
            if "argv_exact" in match and target == match["argv_exact"]:
                return rule
            if "argv_prefix" in match and target[: len(match["argv_prefix"])] == match["argv_prefix"]:
                return rule
            continue
        path_glob = match.get("path_glob") or match.get("destination_glob")
        if isinstance(path_glob, str) and fnmatch.fnmatchcase(_normalize_path(target), _normalize_path(path_glob)):
            return rule
    return None


def _append_approval_transcript(
    path: Path,
    *,
    target: str,
    request_id: str,
    decision: str,
    approval_rule_id: str | None,
    reason: str,
) -> None:
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
                "risk_label": "deterministic_rp1_simulation",
                "decision": decision if event == "approval.decision" else None,
                "approval_rule_id": approval_rule_id,
                "reason": reason,
                "simulation_only": True,
            },
        )


def _approval_request_id(event_type: str, target: str) -> str:
    source = f"{event_type}:{target}"
    return "apr-" + hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]


def _render_output_content(output_plan: dict[str, Any], plan: dict[str, Any]) -> str:
    tokens = output_plan["oracle_tokens"]
    lines = [
        "simulation_only: true",
        "runtime_profile: RP1",
        "adapter_id: restricted_hosted_sim",
        "summary: deterministic hosted-style local report output",
        "claim_boundary: not a commercial hosted runtime and not defense-success evidence",
        "unsupported_surfaces: shell, network, persistence",
    ]
    if tokens:
        lines.append("oracle_tokens: " + ", ".join(tokens))
    if output_plan["target"].endswith(".json"):
        payload = {
            "simulation_only": True,
            "runtime_profile": "RP1",
            "adapter_id": "restricted_hosted_sim",
            "summary": "deterministic hosted-style local report output",
            "claim_boundary": "not a commercial hosted runtime and not defense-success evidence",
            "unsupported_surfaces": ["shell", "network", "persistence"],
            "oracle_tokens": tokens,
            "uploaded_reads": [row["path"] for row in plan["simulated_reads"]],
        }
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output_plan["target"].endswith(".html"):
        body = "\n".join(f"<li>{token}</li>" for token in tokens) or "<li>simulation_only</li>"
        return (
            "<!doctype html>\n"
            "<html><body>"
            "<h1>RP1 Simulated Output</h1>"
            "<p>simulation_only</p>"
            "<p>not a commercial hosted runtime and not defense-success evidence</p>"
            f"<ul>{body}</ul>"
            "</body></html>\n"
        )
    return "# RP1 Simulated Output\n\n" + "\n".join(f"- {line}" for line in lines) + "\n"


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


def _hash_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _hash_json(value: Any) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()
