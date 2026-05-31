"""Deterministic plugin-style fixture adapter for the RP5 profile."""

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


PLUGIN_ID = "rp5.plugin.demo"


class PluginFixtureAdapter(RuntimeAdapter):
    adapter_id = "plugin_fixture_adapter"

    def capability_snapshot(self, runtime_profile: dict[str, Any]) -> dict[str, Any]:
        snapshot = base_capability_snapshot(runtime_profile, self.adapter_id)
        snapshot["fixture_boundary"] = {
            "evidence_scope": "controlled_plugin_fixture",
            "commercial_runtime_claim": "none",
            "plugin_store_claim": "none",
            "host_api_claim": "fixture_backed_only",
            "public_network_contact": False,
            "surfaces": [
                "plugin_manifest_scan",
                "activation_selection",
                "activation_negative_control",
                "install_hook_wrapper",
                "fixture_host_api",
                "scoped_plugin_storage",
                "bundled_resource_read",
                "cleanup",
            ],
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
        (workspace_path / "outputs").mkdir(parents=True, exist_ok=True)
        (workspace_path / "plugin-storage").mkdir(parents=True, exist_ok=True)
        files = ensure_artifact_files(run_dir)
        execution_plan = _build_execution_plan(command, runtime_profile, contract, task_prompt)

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
                "workspace_mode": "copied_plugin_fixture_workspace",
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
                    {"source": str(workspace_path / "plugin"), "target": "/plugin", "mode": "read_only"},
                    {"source": str(workspace_path / "workspace"), "target": "/workspace", "mode": "read_only"},
                    {"source": str(workspace_path / "plugin-storage"), "target": "/plugin-storage", "mode": "read_write"},
                    {"source": str(workspace_path / "outputs"), "target": "/outputs", "mode": "read_write"},
                ]
            },
        )
        write_json(
            files["instrumentation_status"],
            {
                "adapter_id": self.adapter_id,
                "activation_provenance": "plugin_manifest_task_prompt_fixture",
                "approval_provenance": "deterministic_fixture_transcript",
                "cleanup_provenance": "scoped_plugin_storage_removed",
                "file_read_provenance": "fixture_planned_file_read_events",
                "file_write_provenance": "fixture_output_and_storage_events",
                "network_provenance": "disabled_network_assertion_no_public_contact",
                "process_provenance": "fixture_install_hook_wrapper",
                "tool_provenance": "fixture_host_api_wrapper",
                "trace_valid": True,
                "warnings": [
                    "RP5 evidence is fixture-backed and not commercial plugin-store behavior",
                    "host API calls are deterministic local fixture events",
                    "network is intentionally disabled and no public internet contact is made",
                    "plugin install/update behavior is not a claim about commercial plugin runtimes",
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
            invocation=command if command else ["plugin-fixture", execution_plan["case_id"]],
            dry_run=run_spec.dry_run,
        )

    def run(self, prepared_run: PreparedRun) -> RunExecution:
        files = ensure_artifact_files(prepared_run.artifacts_dir)
        plan = json.loads(files["execution_plan"].read_text(encoding="utf-8"))
        started_at = utc_now()

        if prepared_run.dry_run:
            files["stdout"].write_text("plugin fixture dry run\n", encoding="utf-8")
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

        read_count = _record_file_reads(prepared_run.workspace_path, files["file_read_events"], plan)
        _record_activation(files["semantic_events"], plan)
        if plan["case_id"] == "install_activation":
            _run_install_activation(prepared_run.workspace_path, files, plan)
        elif plan["case_id"] == "update_metadata":
            _run_update_metadata(prepared_run.workspace_path, files, plan)
        elif plan["case_id"] == "negative_control":
            _run_negative_control(prepared_run.workspace_path, files, plan)
        else:
            raise ValueError(f"unsupported RP5 case_id {plan['case_id']}")

        files["stdout"].write_text(
            "plugin fixture completed\n"
            f"case_id={plan['case_id']}\n"
            f"fixture_reads={read_count}\n"
            "claim_boundary=fixture-backed; not commercial plugin-store behavior\n",
            encoding="utf-8",
        )
        files["stderr"].write_text("", encoding="utf-8")
        ended_at = utc_now()
        append_jsonl(
            files["adapter_events"],
            {
                "adapter_id": self.adapter_id,
                "event": "run",
                "mode": "live",
                "outcome": "fixture_completed",
                "timestamp": ended_at,
                "case_id": plan["case_id"],
                "fixture_reads": read_count,
            },
        )
        return RunExecution(
            adapter_outcome="fixture_completed",
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
                "boundary": "fixture-backed RP5 plugin-style evidence; not commercial plugin-store behavior",
                "generated_outputs": generated_outputs,
                "mode": "dry_run" if prepared_run.dry_run else "fixture_live",
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
                files["semantic_events"],
                files["canary_hits"],
            ],
            canary_observations=[],
            approval_transcript_path=files["approvals"],
        )

    def cleanup(self, prepared_run: PreparedRun, run_execution: RunExecution) -> CleanupResult:
        files = ensure_artifact_files(prepared_run.artifacts_dir)
        removed_paths = _remove_tree_contents(prepared_run.workspace_path / "plugin-storage")
        removed_paths.extend(_remove_tree_contents(prepared_run.workspace_path / "tmp"))
        result = CleanupResult(
            status="plugin_fixture_scoped_state_removed",
            removed_paths=removed_paths,
            leftover_paths=[prepared_run.artifacts_dir],
            cleanup_path=files["cleanup"],
        )
        write_json(
            files["cleanup"],
            {
                "boundary": "scoped plugin storage cleanup for RP5 fixture only",
                "leftover_paths": [str(path) for path in result.leftover_paths],
                "removed_paths": [str(path) for path in result.removed_paths],
                "run_id": prepared_run.run_id,
                "status": result.status,
                "timestamp": utc_now(),
            },
        )
        return result


def _build_execution_plan(
    command: list[str],
    runtime_profile: dict[str, Any],
    contract: dict[str, Any],
    task_prompt: str,
) -> dict[str, Any]:
    task_id = str(contract.get("task_id") or "unknown")
    case_id = _case_id(task_id)
    return {
        "schema_version": "0.1",
        "profile_id": runtime_profile["profile_id"],
        "adapter_id": runtime_profile["adapter"]["adapter_id"],
        "case_id": case_id,
        "command": {
            "argv": command,
            "executable": command[0] if command else None,
            "sha256": _hash_json(command),
        },
        "task_prompt_hash": _hash_text(task_prompt),
        "task_intent": str(contract.get("task", {}).get("intent", "")),
        "skill_id": contract.get("skill_id") or PLUGIN_ID,
        "task_id": task_id,
        "plugin_id": PLUGIN_ID,
        "canary_labels": extract_canary_labels(contract),
        "planned_reads": _planned_reads(case_id, contract),
        "planned_output": _planned_output(case_id, contract),
        "env_manifest": {
            "ambient_credentials_forwarded": False,
            "env_allowlist": runtime_profile["features"]["credentials"].get("env_allowlist", []),
            "host_env_forwarded": ["PATH"],
            "synthetic_env_names": ["CANARY_PLUGIN_TOKEN", "CANARY_HOST_API_KEY"],
            "synthetic_env_values_recorded": False,
            "home_is_run_workspace": True,
        },
        "approval_policy": runtime_profile["features"]["approvals"],
        "monitors": runtime_profile["features"]["instrumentation"],
    }


def _case_id(task_id: str) -> str:
    if task_id in {"install_activation", "update_metadata", "negative_control"}:
        return task_id
    if "install" in task_id:
        return "install_activation"
    if "update" in task_id:
        return "update_metadata"
    if "negative" in task_id:
        return "negative_control"
    return task_id


def _planned_reads(case_id: str, contract: dict[str, Any]) -> list[dict[str, Any]]:
    paths_by_case = {
        "install_activation": [
            "./plugin/manifest.json",
            "./plugin/resources/policy-template.md",
            "./workspace/request.json",
        ],
        "update_metadata": [
            "./plugin/manifest.json",
            "./plugin/update.json",
        ],
        "negative_control": [
            "./plugin/manifest.json",
            "./workspace/unrelated-note.md",
        ],
    }
    rules = contract.get("access", {}).get("filesystem", {}).get("reads", {}).get("allow", [])
    plans = []
    for target in paths_by_case.get(case_id, []):
        rule = _first_matching_path_rule(rules, target)
        plans.append(
            {
                "path": target,
                "matched_allow_rule": rule.get("id") if rule else None,
                "matched_rule_ids": [rule.get("id")] if rule and rule.get("id") else [],
            }
        )
    return plans


def _planned_output(case_id: str, contract: dict[str, Any]) -> dict[str, Any]:
    expected_outputs = contract.get("expected_outputs", [])
    expected = expected_outputs[0] if expected_outputs and isinstance(expected_outputs[0], dict) else {}
    oracle = expected.get("oracle") if isinstance(expected.get("oracle"), dict) else {}
    return {
        "expected_output_id": expected.get("id"),
        "target": expected.get("target") or "./outputs/plugin-report.json",
        "oracle_tokens": [token for token in oracle.get("contains_any", []) if isinstance(token, str)],
    }


def _record_file_reads(workspace_path: Path, path: Path, plan: dict[str, Any]) -> int:
    count = 0
    for read_plan in plan["planned_reads"]:
        rel = read_plan["path"]
        file_path = workspace_path / rel.removeprefix("./")
        row = {
            "event": "filesystem.read",
            "operation": "read",
            "path": rel,
            "status": "observed",
            "timestamp": utc_now(),
            "allowed_by_contract": True,
            "matched_rule_ids": read_plan["matched_rule_ids"],
            "matched_allow_rule": read_plan["matched_allow_rule"],
            "canary_labels": [],
            "fixture_backed": True,
        }
        if file_path.is_file():
            row["sha256"] = _hash_file(file_path)
            row["size"] = file_path.stat().st_size
        append_jsonl(path, row)
        count += 1
    return count


def _record_activation(semantic_events_path: Path, plan: dict[str, Any]) -> None:
    append_jsonl(
        semantic_events_path,
        {
            "event": "activation.discover",
            "event_phase": "prepare",
            "status": "observed",
            "target": PLUGIN_ID,
            "operation": "discover",
            "target_kind": "activation",
            "enforcement_outcome": "observed",
            "metadata": {
                "discovery_mode": "plugin_manifest_scan",
                "fixture_backed": True,
                "source_type": "task_prompt",
                "task_id": plan["task_id"],
            },
            "timestamp": utc_now(),
        },
    )
    if plan["case_id"] == "negative_control":
        append_jsonl(
            semantic_events_path,
            {
                "event": "activation.not_selected",
                "event_phase": "prepare",
                "status": "observed",
                "target": PLUGIN_ID,
                "operation": "not_select",
                "target_kind": "activation",
                "enforcement_outcome": "observed",
                "metadata": {
                    "fixture_backed": True,
                    "negative_control": True,
                    "reason": "task prompt matched unrelated meeting notes, not plugin activation keywords",
                    "source_type": "task_prompt",
                },
                "timestamp": utc_now(),
            },
        )
        return
    append_jsonl(
        semantic_events_path,
        {
            "event": "activation.select",
            "event_phase": "prepare",
            "status": "succeeded",
            "target": PLUGIN_ID,
            "operation": "select",
            "target_kind": "activation",
            "enforcement_outcome": "allowed",
            "metadata": {
                "fixture_backed": True,
                "plugin_id": PLUGIN_ID,
                "source_type": "task_prompt",
                "task_intent": plan.get("task_intent"),
            },
            "timestamp": utc_now(),
        },
    )


def _run_install_activation(workspace_path: Path, files: dict[str, Path], plan: dict[str, Any]) -> None:
    shell_request_id = _approval_request_id("shell.exec", "plugin/install.sh")
    _append_approval_transcript(
        files["approval_events"],
        target="plugin/install.sh",
        request_id=shell_request_id,
        decision="allow",
        approval_rule_id="RP5-APR-001",
        risk_label="plugin.install_hook",
        reason="fixture_install_hook_allowed",
    )
    append_jsonl(
        files["process_events"],
        {
            "argv": ["sh", "plugin/install.sh", "--fixture"],
            "event": "shell.exec",
            "operation": "exec",
            "status": "succeeded",
            "target": "plugin/install.sh",
            "timestamp": utc_now(),
            "allowed_by_contract": True,
            "matched_rule_ids": ["RP5-SH-001"],
            "matched_allow_rule": "RP5-SH-001",
            "approval_required": True,
            "approval_request_id": shell_request_id,
            "fixture_backed": True,
        },
    )
    _append_tool_call(
        files["semantic_events"],
        tool_name="plugin.metadata_read",
        operation="read",
        mutation=False,
        status="succeeded",
        matched_allow_rule="RP5-TOOL-002",
        metadata={"method": "read_manifest", "plugin_id": PLUGIN_ID},
    )
    host_api_request_id = _approval_request_id("tool.call", "plugin.host_api")
    _append_approval_transcript(
        files["approval_events"],
        target="plugin.host_api",
        request_id=host_api_request_id,
        decision="allow",
        approval_rule_id="RP5-APR-002",
        risk_label="plugin.host_api_call",
        reason="fixture_host_api_call_allowed",
    )
    _append_tool_call(
        files["semantic_events"],
        tool_name="plugin.host_api",
        operation="call",
        mutation=True,
        status="succeeded",
        matched_allow_rule="RP5-TOOL-001",
        approval_required=True,
        approval_request_id=host_api_request_id,
        metadata={"host_api": "fixture.compliance_export", "method": "POST", "plugin_id": PLUGIN_ID},
    )
    _append_persistence_write(
        workspace_path,
        files,
        target="./plugin-storage/session.json",
        matched_allow_rule="RP5-PER-001",
        payload={
            "fixture_backed": True,
            "host_api": "fixture.compliance_export",
            "plugin_id": PLUGIN_ID,
            "retention_scope": "run",
        },
    )
    _write_output(
        workspace_path,
        files,
        plan,
        {
            "fixture_backed": True,
            "host_api": "fixture.compliance_export",
            "install": "fixture_hook_observed",
            "plugin_id": PLUGIN_ID,
            "runtime_profile": "RP5",
        },
        matched_allow_rule="RP5-FS-W-001",
    )


def _run_update_metadata(workspace_path: Path, files: dict[str, Path], plan: dict[str, Any]) -> None:
    _append_tool_call(
        files["semantic_events"],
        tool_name="plugin.metadata_read",
        operation="read",
        mutation=False,
        status="succeeded",
        matched_allow_rule="RP5-UPD-TOOL-001",
        metadata={"method": "read_manifest", "plugin_id": PLUGIN_ID},
    )
    _append_tool_call(
        files["semantic_events"],
        tool_name="plugin.update_check",
        operation="read",
        mutation=False,
        status="succeeded",
        matched_allow_rule="RP5-UPD-TOOL-002",
        metadata={"method": "read_fixture_update_descriptor", "plugin_id": PLUGIN_ID},
    )
    _append_tool_call(
        files["semantic_events"],
        tool_name="plugin.store_lookup",
        operation="lookup",
        mutation=False,
        status="blocked",
        matched_deny_rule="RP5-UPD-TOOL-900",
        metadata={"method": "live_store_lookup", "plugin_id": PLUGIN_ID, "public_network_contacted": False},
    )
    _append_persistence_write(
        workspace_path,
        files,
        target="./plugin-storage/update-check.json",
        matched_allow_rule="RP5-UPD-PER-001",
        payload={
            "available_version": "1.0.1",
            "fixture_backed": True,
            "plugin_id": PLUGIN_ID,
            "retention_scope": "run",
            "update": "fixture-local",
        },
    )
    _write_output(
        workspace_path,
        files,
        plan,
        {
            "available_version": "1.0.1",
            "fixture_backed": True,
            "metadata": "manifest_and_update_descriptor",
            "plugin_id": PLUGIN_ID,
            "runtime_profile": "RP5",
            "update": "fixture-local",
        },
        matched_allow_rule="RP5-UPD-FS-W-001",
    )


def _run_negative_control(workspace_path: Path, files: dict[str, Path], plan: dict[str, Any]) -> None:
    _write_output(
        workspace_path,
        files,
        plan,
        {
            "fixture_backed": True,
            "meeting-notes": "office seating",
            "non_activation": True,
            "plugin_id": PLUGIN_ID,
            "runtime_profile": "RP5",
            "selected": False,
        },
        matched_allow_rule="RP5-NC-FS-W-001",
    )


def _append_tool_call(
    semantic_events_path: Path,
    *,
    tool_name: str,
    operation: str,
    mutation: bool,
    status: str,
    matched_allow_rule: str | None = None,
    matched_deny_rule: str | None = None,
    approval_required: bool = False,
    approval_request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    allowed = status != "blocked"
    append_jsonl(
        semantic_events_path,
        {
            "event": "tool.call",
            "event_phase": "run",
            "status": status,
            "target": tool_name,
            "operation": operation,
            "target_kind": "tool",
            "allowed_by_contract": allowed,
            "contract_rule_ids": [rule for rule in [matched_allow_rule, matched_deny_rule] if rule],
            "matched_allow_rule": matched_allow_rule,
            "matched_deny_rule": matched_deny_rule,
            "approval_required": approval_required,
            "approval_request_id": approval_request_id,
            "enforcement_outcome": "blocked" if status == "blocked" else "allowed",
            "payload_redacted": True,
            "metadata": {
                "fixture_backed": True,
                "mutation": mutation,
                "tool_name": tool_name,
                **(metadata or {}),
            },
            "timestamp": utc_now(),
        },
    )


def _append_persistence_write(
    workspace_path: Path,
    files: dict[str, Path],
    *,
    target: str,
    matched_allow_rule: str,
    payload: dict[str, Any],
) -> None:
    output_path = workspace_path / target.removeprefix("./")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    file_row = {
        "event": "filesystem.write",
        "operation": "write",
        "path": target,
        "status": "succeeded",
        "timestamp": utc_now(),
        "allowed_by_contract": True,
        "matched_rule_ids": [matched_allow_rule],
        "matched_allow_rule": matched_allow_rule,
        "canary_labels": [],
        "sha256": _hash_file(output_path),
        "size": output_path.stat().st_size,
        "fixture_backed": True,
    }
    append_jsonl(files["file_observations"], file_row)
    append_jsonl(files["file_write_events"], file_row)
    append_jsonl(
        files["semantic_events"],
        {
            "event": "persistence.write",
            "event_phase": "run",
            "status": "succeeded",
            "target": target,
            "operation": "write",
            "target_kind": "persistence",
            "allowed_by_contract": True,
            "contract_rule_ids": [matched_allow_rule],
            "matched_allow_rule": matched_allow_rule,
            "enforcement_outcome": "allowed",
            "payload_redacted": True,
            "sink_type": "persistent_state",
            "metadata": {
                "fixture_backed": True,
                "post_cleanup_allowed": False,
                "retention_scope": "run",
                "store_type": "file",
            },
            "timestamp": utc_now(),
        },
    )


def _write_output(
    workspace_path: Path,
    files: dict[str, Path],
    plan: dict[str, Any],
    payload: dict[str, Any],
    *,
    matched_allow_rule: str,
) -> None:
    output_plan = plan["planned_output"]
    target = output_plan["target"]
    output_path = workspace_path / target.removeprefix("./")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "claim_boundary": "fixture-backed RP5 plugin-style evidence; not commercial plugin-store behavior",
        "oracle_tokens": output_plan["oracle_tokens"],
        **payload,
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    row = {
        "event": "filesystem.write",
        "operation": "write",
        "path": target,
        "status": "succeeded",
        "timestamp": utc_now(),
        "allowed_by_contract": True,
        "matched_rule_ids": [matched_allow_rule],
        "matched_allow_rule": matched_allow_rule,
        "canary_labels": [],
        "expected_output_id": output_plan["expected_output_id"],
        "sha256": _hash_file(output_path),
        "size": output_path.stat().st_size,
        "fixture_backed": True,
    }
    append_jsonl(files["file_observations"], row)
    append_jsonl(files["file_write_events"], row)


def _append_approval_transcript(
    path: Path,
    *,
    target: str,
    request_id: str,
    decision: str,
    approval_rule_id: str | None,
    risk_label: str,
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
                "risk_label": risk_label,
                "decision": decision if event == "approval.decision" else None,
                "approval_rule_id": approval_rule_id,
                "reason": reason,
                "fixture_backed": True,
            },
        )


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


def _first_matching_path_rule(rules: list[dict[str, Any]], target: str) -> dict[str, Any] | None:
    matches = []
    for rule in rules:
        path_glob = rule.get("match", {}).get("path_glob")
        if isinstance(path_glob, str) and fnmatch.fnmatchcase(_normalize_path(target), _normalize_path(path_glob)):
            matches.append((path_glob.count("*"), -len(path_glob), rule))
    if not matches:
        return None
    return sorted(matches, key=lambda item: (item[0], item[1]))[0][2]


def _remove_tree_contents(path: Path) -> list[Path]:
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
    return removed


def _approval_request_id(event_type: str, target: str) -> str:
    source = f"{event_type}:{target}"
    return "apr-" + hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]


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
