"""Canonical trace event construction and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
import hashlib
import json
import re

from skilldiff.adapters.base import CleanupResult, CollectedRun, PreparedRun, RunExecution, utc_now


SCHEMA_VERSION = "0.1"
EVENT_TYPES = {
    "run.start",
    "run.end",
    "capability.snapshot",
    "activation.discover",
    "activation.select",
    "activation.not_selected",
    "filesystem.read",
    "filesystem.write",
    "filesystem.modify",
    "filesystem.delete",
    "shell.exec",
    "process.exec",
    "process.exit",
    "network.connect",
    "network.send",
    "tool.call",
    "approval.required",
    "approval.prompt",
    "approval.decision",
    "context.read",
    "credential.read",
    "output.generated",
    "log.write",
    "persistence.write",
    "persistence.observe",
    "cleanup.observe",
    "canary.inject",
    "canary.observe",
    "canary.sink_match",
    "instrumentation.failure",
}
EVENT_PHASES = {"prepare", "run", "collect", "cleanup", "normalize"}
EVENT_STATUSES = {"attempted", "blocked", "succeeded", "failed", "observed", "not_executed"}
TARGET_KINDS = {
    "run",
    "capability",
    "activation",
    "filesystem",
    "process",
    "network",
    "tool",
    "approval",
    "context",
    "credential",
    "output",
    "log",
    "persistence",
    "cleanup",
    "canary",
    "instrumentation",
    "unknown",
}
ENFORCEMENT_OUTCOMES = {"allowed", "blocked", "failed", "observed", "not_applicable", "unknown"}
REQUIRED_FIELDS = {
    "schema_version",
    "run_id",
    "event_id",
    "timestamp",
    "event_type",
    "event_phase",
    "actor",
    "event_status",
    "skill_id",
    "task_id",
    "contract_id",
    "runtime_profile",
    "runtime_profile_hash",
    "adapter_id",
    "adapter_version",
    "repeat_id",
    "target",
    "normalized_target",
    "target_kind",
    "operation",
    "allowed_by_contract",
    "contract_rule_ids",
    "matched_allow_rule",
    "matched_deny_rule",
    "approval_required",
    "approval_request_id",
    "parent_event_id",
    "enforcement_outcome",
    "canary_observed",
    "canary_labels",
    "sink_type",
    "payload_hash",
    "payload_redacted",
    "evidence_ref",
    "metadata",
}


class TraceValidationError(Exception):
    """Trace validation failed."""


@dataclass(frozen=True)
class TraceContext:
    run_id: str
    skill_id: str
    task_id: str
    contract_id: str
    runtime_profile: str
    runtime_profile_hash: str
    adapter_id: str
    adapter_version: str
    repeat_id: int


class TraceBuilder:
    """Build a canonical trace from adapter artifacts."""

    def __init__(self, context: TraceContext) -> None:
        self.context = context
        self._events: list[dict[str, Any]] = []

    @classmethod
    def from_run_metadata(cls, metadata: dict[str, Any]) -> "TraceBuilder":
        return cls(
            TraceContext(
                run_id=metadata["run_id"],
                skill_id=metadata["skill_id"],
                task_id=metadata["task_id"],
                contract_id=metadata["contract_id"],
                runtime_profile=metadata["profile_id"],
                runtime_profile_hash=metadata["profile_hash"],
                adapter_id=metadata["adapter_id"],
                adapter_version=metadata.get("adapter_version", "0.1"),
                repeat_id=int(metadata.get("repeat_id", 0)),
            )
        )

    def add(
        self,
        event_type: str,
        *,
        event_phase: str,
        actor: str,
        event_status: str,
        target_kind: str,
        target: str | None = None,
        normalized_target: str | None = None,
        operation: str | None = None,
        allowed_by_contract: bool | None = None,
        contract_rule_ids: list[str] | None = None,
        matched_allow_rule: str | None = None,
        matched_deny_rule: str | None = None,
        approval_required: bool | None = None,
        approval_request_id: str | None = None,
        parent_event_id: str | None = None,
        enforcement_outcome: str = "unknown",
        canary_labels: list[str] | None = None,
        sink_type: str | None = None,
        payload: bytes | str | None = None,
        payload_hash_override: str | None = None,
        payload_redacted: bool = True,
        evidence_ref: str | None = None,
        metadata: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> str:
        if event_type not in EVENT_TYPES:
            raise TraceValidationError(f"unknown event_type {event_type}")
        if event_phase not in EVENT_PHASES:
            raise TraceValidationError(f"unknown event_phase {event_phase}")
        if event_status not in EVENT_STATUSES:
            raise TraceValidationError(f"unknown event_status {event_status}")
        if target_kind not in TARGET_KINDS:
            raise TraceValidationError(f"unknown target_kind {target_kind}")
        if enforcement_outcome not in ENFORCEMENT_OUTCOMES:
            raise TraceValidationError(f"unknown enforcement_outcome {enforcement_outcome}")

        labels = sorted(set(canary_labels or []))
        event_id = f"evt-{len(self._events) + 1:06d}"
        event = {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.context.run_id,
            "event_id": event_id,
            "timestamp": timestamp or utc_now(),
            "event_type": event_type,
            "event_phase": event_phase,
            "actor": actor,
            "event_status": event_status,
            "skill_id": self.context.skill_id,
            "task_id": self.context.task_id,
            "contract_id": self.context.contract_id,
            "runtime_profile": self.context.runtime_profile,
            "runtime_profile_hash": self.context.runtime_profile_hash,
            "adapter_id": self.context.adapter_id,
            "adapter_version": self.context.adapter_version,
            "repeat_id": self.context.repeat_id,
            "target": target,
            "normalized_target": normalized_target or normalize_target(target),
            "target_kind": target_kind,
            "operation": operation,
            "allowed_by_contract": allowed_by_contract,
            "contract_rule_ids": contract_rule_ids or [],
            "matched_allow_rule": matched_allow_rule,
            "matched_deny_rule": matched_deny_rule,
            "approval_required": approval_required,
            "approval_request_id": approval_request_id,
            "parent_event_id": parent_event_id,
            "enforcement_outcome": enforcement_outcome,
            "canary_observed": bool(labels),
            "canary_labels": labels,
            "sink_type": sink_type,
            "payload_hash": payload_hash_override or (hash_payload(payload) if payload is not None else None),
            "payload_redacted": payload_redacted,
            "evidence_ref": evidence_ref,
            "metadata": metadata or {},
        }
        self._events.append(event)
        return event_id

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for event in self._events:
                handle.write(json.dumps(event, sort_keys=True) + "\n")

    @property
    def events(self) -> list[dict[str, Any]]:
        return list(self._events)


def build_trace_from_artifacts(
    prepared_run: PreparedRun,
    run_execution: RunExecution,
    collected_run: CollectedRun,
    cleanup_result: CleanupResult,
    contract: dict[str, Any],
) -> Path:
    metadata = json.loads(prepared_run.run_metadata_path.read_text(encoding="utf-8"))
    builder = TraceBuilder.from_run_metadata(metadata)
    canary_labels = extract_canary_labels(contract)

    builder.add(
        "run.start",
        event_phase="prepare",
        actor=prepared_run.adapter_id,
        event_status="succeeded",
        target_kind="run",
        target=prepared_run.run_id,
        enforcement_outcome="not_applicable",
        evidence_ref=str(prepared_run.run_metadata_path),
        metadata={
            "dry_run": prepared_run.dry_run,
            "workspace_path": str(prepared_run.workspace_path),
            "invocation": prepared_run.invocation,
        },
    )
    builder.add(
        "capability.snapshot",
        event_phase="prepare",
        actor=prepared_run.adapter_id,
        event_status="observed",
        target_kind="capability",
        target=prepared_run.profile_id,
        enforcement_outcome="observed",
        evidence_ref=str(prepared_run.capabilities_path),
    )
    _append_raw_process_events(builder, prepared_run.artifacts_dir / "process_events.jsonl")
    _append_raw_file_read_events(builder, prepared_run.artifacts_dir / "file_read_events.jsonl", canary_labels)
    _append_raw_file_observations(builder, prepared_run.artifacts_dir / "file_observations.jsonl", canary_labels)
    _append_raw_approval_events(builder, prepared_run.artifacts_dir / "approvals.jsonl")
    _append_raw_approval_events(builder, prepared_run.artifacts_dir / "approval_events.jsonl")
    _append_raw_network_events(builder, prepared_run.artifacts_dir / "network_attempts.jsonl", canary_labels)
    _append_raw_network_events(builder, prepared_run.artifacts_dir / "network_events.jsonl", canary_labels)
    _append_raw_instrumentation_events(builder, prepared_run.artifacts_dir / "adapter_events.jsonl")
    _append_output_events(builder, prepared_run.workspace_path, contract, canary_labels)
    _append_canary_hits(builder, prepared_run.artifacts_dir / "canary_hits.jsonl")
    _append_log_canaries(builder, run_execution.stdout_path, "stdout_log", canary_labels)
    _append_log_canaries(builder, run_execution.stderr_path, "stderr_log", canary_labels)

    if run_execution.adapter_outcome != "blocked_by_execution_plan":
        builder.add(
            "process.exit",
            event_phase="run",
            actor=prepared_run.adapter_id,
            event_status="succeeded" if run_execution.exit_code == 0 else "failed",
            target_kind="process",
            target=prepared_run.invocation[0] if prepared_run.invocation else None,
            operation="exit",
            enforcement_outcome="allowed" if run_execution.exit_code == 0 else "failed",
            evidence_ref=str(run_execution.adapter_events_path),
            metadata={
                "exit_code": run_execution.exit_code,
                "adapter_outcome": run_execution.adapter_outcome,
                "started_at": run_execution.started_at,
                "ended_at": run_execution.ended_at,
            },
        )
    builder.add(
        "cleanup.observe",
        event_phase="cleanup",
        actor=prepared_run.adapter_id,
        event_status="observed",
        target_kind="cleanup",
        target=cleanup_result.status,
        enforcement_outcome="observed",
        evidence_ref=str(cleanup_result.cleanup_path),
        metadata={
            "removed_paths": [str(path) for path in cleanup_result.removed_paths],
            "leftover_paths": [str(path) for path in cleanup_result.leftover_paths],
        },
    )
    builder.add(
        "run.end",
        event_phase="cleanup",
        actor=prepared_run.adapter_id,
        event_status="succeeded" if run_execution.exit_code == 0 else "failed",
        target_kind="run",
        target=prepared_run.run_id,
        enforcement_outcome="not_applicable",
        evidence_ref=str(prepared_run.artifacts_dir / "trace.jsonl"),
        metadata={"exit_code": run_execution.exit_code, "adapter_outcome": run_execution.adapter_outcome},
    )

    trace_path = prepared_run.artifacts_dir / "trace.jsonl"
    builder.write(trace_path)
    events = validate_trace_file(trace_path)
    manifest_path = prepared_run.artifacts_dir / "trace_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "event_count": len(events),
                "event_types": sorted({event["event_type"] for event in events}),
                "run_id": prepared_run.run_id,
                "schema_version": SCHEMA_VERSION,
                "trace_path": str(trace_path),
                "trace_valid": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return trace_path


def validate_trace_file(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    event_ids: set[str] = set()
    run_ids: set[str] = set()
    has_start = False
    has_end = False
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise TraceValidationError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            _validate_event(event, path, line_number)
            if event["event_id"] in event_ids:
                raise TraceValidationError(f"{path}:{line_number}: duplicate event_id {event['event_id']}")
            event_ids.add(event["event_id"])
            run_ids.add(event["run_id"])
            has_start = has_start or event["event_type"] == "run.start"
            has_end = has_end or event["event_type"] == "run.end"
            events.append(event)
    if not events:
        raise TraceValidationError(f"{path}: trace is empty")
    if len(run_ids) != 1:
        raise TraceValidationError(f"{path}: expected exactly one run_id, got {sorted(run_ids)}")
    if not has_start or not has_end:
        raise TraceValidationError(f"{path}: trace requires run.start and run.end")
    if events[0]["event_type"] != "run.start":
        raise TraceValidationError(f"{path}: first event must be run.start")
    if events[-1]["event_type"] != "run.end":
        raise TraceValidationError(f"{path}: last event must be run.end")
    _validate_instrumentation_status(path)
    return events


def extract_canary_labels(contract: dict[str, Any]) -> list[str]:
    labels = []
    for canary in contract.get("canaries", []):
        label = canary.get("label")
        if isinstance(label, str):
            labels.append(label)
    return sorted(set(labels))


def scan_text_for_canaries(text: str, labels: Iterable[str]) -> list[str]:
    return sorted(label for label in set(labels) if label and label in text)


def hash_payload(payload: bytes | str) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8", errors="replace")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def normalize_target(target: str | None) -> str | None:
    if target is None:
        return None
    if target.startswith(("env:", "cred:")):
        return target
    if target.startswith("http://") or target.startswith("https://"):
        return target.lower()
    prefix = "./" if target.startswith("./") or not target.startswith(("/", "~")) else ""
    raw = target[2:] if target.startswith("./") else target
    parts: list[str] = []
    for part in re.split(r"/+", raw):
        if part in {"", "."}:
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    if target.startswith("/"):
        return "/" + "/".join(parts)
    if target.startswith("~/"):
        return "~/" + "/".join(parts[1:] if parts[:1] == ["~"] else parts)
    return prefix + "/".join(parts)


def snapshot_tree(root: Path) -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}
    if not root.exists():
        return snapshot
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = "./" + path.relative_to(root).as_posix()
            snapshot[rel] = {"size": path.stat().st_size, "sha256": hash_file(path)}
    return snapshot


def diff_snapshots(
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for path in sorted(set(after) - set(before)):
        observations.append({"event": "filesystem.write", "operation": "write", "path": path, "status": "succeeded", "sha256": after[path]["sha256"], "size": after[path]["size"]})
    for path in sorted(set(before) & set(after)):
        if before[path]["sha256"] != after[path]["sha256"]:
            observations.append({"event": "filesystem.modify", "operation": "write", "path": path, "status": "succeeded", "before_sha256": before[path]["sha256"], "sha256": after[path]["sha256"], "size": after[path]["size"]})
    for path in sorted(set(before) - set(after)):
        observations.append({"event": "filesystem.delete", "operation": "delete", "path": path, "status": "succeeded", "before_sha256": before[path]["sha256"]})
    return observations


def _append_raw_file_observations(builder: TraceBuilder, path: Path, canary_labels: list[str]) -> None:
    for row in _read_jsonl(path):
        event_type = row.get("event")
        if event_type not in {"filesystem.write", "filesystem.modify", "filesystem.delete"}:
            continue
        target = row.get("path")
        labels = row.get("canary_labels") or []
        builder.add(
            event_type,
            event_phase="run",
            actor=builder.context.adapter_id,
            event_status=row.get("status", "observed"),
            target_kind="filesystem",
            target=target,
            operation=row.get("operation"),
            enforcement_outcome=_file_write_enforcement_outcome(row.get("status", "observed")),
            canary_labels=labels,
            evidence_ref=str(path),
            metadata={key: value for key, value in row.items() if key not in {"event", "path", "operation", "status", "canary_labels"}},
            timestamp=row.get("timestamp"),
        )


def _append_raw_file_read_events(builder: TraceBuilder, path: Path, canary_labels: list[str]) -> None:
    for row in _read_jsonl(path):
        event_type = row.get("event", "filesystem.read")
        if event_type != "filesystem.read":
            continue
        target = row.get("path")
        labels = row.get("canary_labels") or []
        status = row.get("status", "observed")
        builder.add(
            "filesystem.read",
            event_phase="run",
            actor=builder.context.adapter_id,
            event_status=status,
            target_kind="filesystem",
            target=target,
            operation=row.get("operation", "read"),
            enforcement_outcome=_file_read_enforcement_outcome(status),
            canary_labels=labels,
            evidence_ref=str(path),
            metadata={key: value for key, value in row.items() if key not in {"event", "path", "operation", "status", "canary_labels"}},
            timestamp=row.get("timestamp"),
        )


def _file_read_enforcement_outcome(status: str) -> str:
    if status == "blocked":
        return "blocked"
    if status == "failed":
        return "failed"
    if status == "not_executed":
        return "not_applicable"
    return "observed"


def _file_write_enforcement_outcome(status: str) -> str:
    if status == "blocked":
        return "blocked"
    if status == "failed":
        return "failed"
    if status == "not_executed":
        return "not_applicable"
    return "observed"


def _append_raw_process_events(builder: TraceBuilder, path: Path) -> None:
    for row in _read_jsonl(path):
        event_type = row.get("event")
        if event_type not in {"shell.exec", "process.exec"}:
            continue
        status = row.get("status", "attempted")
        builder.add(
            event_type,
            event_phase="run",
            actor=builder.context.adapter_id,
            event_status=status,
            target_kind="process",
            target=row.get("target"),
            operation=row.get("operation", "exec"),
            enforcement_outcome="blocked" if status == "blocked" else "allowed",
            contract_rule_ids=[rule_id for rule_id in row.get("matched_rule_ids", []) if rule_id],
            evidence_ref=str(path),
            metadata={key: value for key, value in row.items() if key not in {"event", "target", "operation", "status"}},
        )


def _append_raw_approval_events(builder: TraceBuilder, path: Path) -> None:
    for row in _read_jsonl(path):
        event_type = row.get("event", "approval.decision")
        if event_type not in {"approval.required", "approval.prompt", "approval.decision"}:
            event_type = "approval.decision"
        builder.add(
            event_type,
            event_phase="run",
            actor=builder.context.adapter_id,
            event_status=row.get("status", "observed"),
            target_kind="approval",
            target=row.get("target"),
            operation=row.get("operation"),
            approval_request_id=row.get("approval_request_id"),
            enforcement_outcome=row.get("enforcement_outcome", "observed"),
            evidence_ref=str(path),
            metadata=row,
        )


def _append_raw_network_events(builder: TraceBuilder, path: Path, canary_labels: list[str]) -> None:
    for row in _read_jsonl(path):
        payload = row.get("payload_redacted_excerpt")
        labels = sorted(set((row.get("canary_labels") or []) + scan_text_for_canaries(str(payload or ""), canary_labels)))
        metadata = {
            key: value
            for key, value in row.items()
            if key not in {"event", "payload_redacted_excerpt", "canary_labels"}
        }
        builder.add(
            row.get("event", "network.connect"),
            event_phase="run",
            actor=builder.context.adapter_id,
            event_status=row.get("status", "attempted"),
            target_kind="network",
            target=row.get("domain") or row.get("url"),
            normalized_target=row.get("domain") or row.get("url"),
            operation=row.get("operation", "connect"),
            enforcement_outcome=row.get("enforcement_outcome", "unknown"),
            canary_labels=labels,
            sink_type=row.get("sink_type", "external_http"),
            payload=None,
            payload_hash_override=row.get("payload_hash"),
            payload_redacted=True,
            evidence_ref=str(path),
            metadata=metadata,
        )


def _append_raw_instrumentation_events(builder: TraceBuilder, path: Path) -> None:
    for row in _read_jsonl(path):
        if row.get("event") != "instrumentation.failure":
            continue
        builder.add(
            "instrumentation.failure",
            event_phase="run",
            actor=builder.context.adapter_id,
            event_status=row.get("status", "failed"),
            target_kind="instrumentation",
            target=row.get("instrumentation_model"),
            operation="observe",
            enforcement_outcome="failed",
            evidence_ref=str(path),
            metadata=row,
            timestamp=row.get("timestamp"),
        )


def _append_output_events(builder: TraceBuilder, workspace_path: Path, contract: dict[str, Any], canary_labels: list[str]) -> None:
    for expected in contract.get("expected_outputs", []):
        target = expected.get("target")
        if not isinstance(target, str) or target.startswith(("~", "/")):
            continue
        output_path = workspace_path / target.removeprefix("./")
        if not output_path.exists() or not output_path.is_file():
            continue
        content = _read_text_safely(output_path)
        labels = scan_text_for_canaries(content, canary_labels)
        builder.add(
            "output.generated",
            event_phase="collect",
            actor=builder.context.adapter_id,
            event_status="observed",
            target_kind="output",
            target=target,
            operation="write",
            enforcement_outcome="observed",
            canary_labels=labels,
            sink_type=_infer_sink_type(target),
            payload=content,
            payload_redacted=True,
            evidence_ref=str(output_path),
            metadata={"expected_output_id": expected.get("id"), "sha256": hash_file(output_path)},
        )
        if labels:
            builder.add(
                "canary.observe",
                event_phase="collect",
                actor="canary_scanner",
                event_status="observed",
                target_kind="canary",
                target=target,
                operation="scan",
                enforcement_outcome="observed",
                canary_labels=labels,
                sink_type=_infer_sink_type(target),
                payload_redacted=True,
                evidence_ref=str(output_path),
            )


def _append_log_canaries(builder: TraceBuilder, path: Path, sink_type: str, canary_labels: list[str]) -> None:
    if not path.exists():
        return
    content = _read_text_safely(path)
    labels = scan_text_for_canaries(content, canary_labels)
    if not labels:
        return
    builder.add(
        "canary.observe",
        event_phase="collect",
        actor="canary_scanner",
        event_status="observed",
        target_kind="canary",
        target=str(path),
        operation="scan",
        enforcement_outcome="observed",
        canary_labels=labels,
        sink_type=sink_type,
        payload_redacted=True,
        evidence_ref=str(path),
    )


def _append_canary_hits(builder: TraceBuilder, path: Path) -> None:
    for row in _read_jsonl(path):
        labels = row.get("labels") or []
        if not labels:
            continue
        builder.add(
            "canary.observe",
            event_phase="collect",
            actor="canary_scanner",
            event_status="observed",
            target_kind="canary",
            target=row.get("path"),
            operation="scan",
            enforcement_outcome="observed",
            canary_labels=labels,
            sink_type=row.get("sink_type"),
            payload_redacted=True,
            evidence_ref=str(path),
            metadata=row,
        )


def _validate_event(event: dict[str, Any], path: Path, line_number: int) -> None:
    missing = sorted(REQUIRED_FIELDS - set(event))
    if missing:
        raise TraceValidationError(f"{path}:{line_number}: missing fields {missing}")
    unknown = sorted(set(event) - REQUIRED_FIELDS)
    if unknown:
        raise TraceValidationError(f"{path}:{line_number}: unknown fields {unknown}")
    if event["event_type"] not in EVENT_TYPES:
        raise TraceValidationError(f"{path}:{line_number}: unknown event_type {event['event_type']}")
    if event["event_phase"] not in EVENT_PHASES:
        raise TraceValidationError(f"{path}:{line_number}: unknown event_phase {event['event_phase']}")
    if event["event_status"] not in EVENT_STATUSES:
        raise TraceValidationError(f"{path}:{line_number}: unknown event_status {event['event_status']}")
    if event["target_kind"] not in TARGET_KINDS:
        raise TraceValidationError(f"{path}:{line_number}: unknown target_kind {event['target_kind']}")
    if event["enforcement_outcome"] not in ENFORCEMENT_OUTCOMES:
        raise TraceValidationError(f"{path}:{line_number}: unknown enforcement_outcome {event['enforcement_outcome']}")
    if not isinstance(event["contract_rule_ids"], list):
        raise TraceValidationError(f"{path}:{line_number}: contract_rule_ids must be a list")
    if not isinstance(event["canary_labels"], list):
        raise TraceValidationError(f"{path}:{line_number}: canary_labels must be a list")
    if event["canary_observed"] and not event["canary_labels"]:
        raise TraceValidationError(f"{path}:{line_number}: canary_observed requires canary_labels")
    if event["event_type"] == "process.exit" and "exit_code" not in event["metadata"]:
        raise TraceValidationError(f"{path}:{line_number}: process.exit requires metadata.exit_code")
    if event["event_type"] in {"network.connect", "network.send"}:
        if event["target_kind"] != "network":
            raise TraceValidationError(f"{path}:{line_number}: network event requires target_kind=network")
        if not event["target"]:
            raise TraceValidationError(f"{path}:{line_number}: network event requires target")
        if event["payload_redacted"] is not True:
            raise TraceValidationError(f"{path}:{line_number}: network event payload must be redacted")
        if event["event_type"] == "network.send" and not event["payload_hash"]:
            raise TraceValidationError(f"{path}:{line_number}: network.send requires payload_hash")
        metadata = event.get("metadata") or {}
        if metadata.get("public_internet_contacted") is True:
            raise TraceValidationError(f"{path}:{line_number}: PV-02 network event must not contact public internet")
        for raw_payload_key in ("payload", "body", "request_body", "raw_payload"):
            if raw_payload_key in metadata:
                raise TraceValidationError(f"{path}:{line_number}: network metadata must not retain raw payload field {raw_payload_key}")


def _validate_instrumentation_status(path: Path) -> None:
    status_path = path.parent / "instrumentation_status.json"
    if not status_path.exists():
        return
    try:
        status = json.loads(status_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TraceValidationError(f"{status_path}: invalid JSON: {exc}") from exc
    if status.get("trace_valid") is False:
        reason = status.get("file_read_provenance", "unknown")
        raise TraceValidationError(f"{path}: instrumentation_status trace_valid=false ({reason})")
    file_read_provenance = status.get("file_read_provenance")
    if isinstance(file_read_provenance, str) and file_read_provenance.endswith("_unavailable"):
        raise TraceValidationError(f"{path}: instrumentation unavailable ({file_read_provenance})")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _read_text_safely(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _infer_sink_type(target: str) -> str:
    normalized = target.replace("\\", "/")
    if normalized.startswith("./docs/") or normalized.startswith("docs/"):
        return "docs_bundle"
    if normalized.startswith("./approved-output/") or normalized.startswith("approved-output/"):
        return "approved_output_tree"
    if normalized.startswith("./repo/") or normalized.startswith("repo/"):
        return "source_tree"
    if target.endswith(".html"):
        return "local_html"
    if target.endswith(".json"):
        return "local_json"
    if "report" in target or "audit" in target:
        return "local_report"
    return "output_tree"
