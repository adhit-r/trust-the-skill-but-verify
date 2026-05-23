"""Runtime adapter boundary for the differential skill-security harness.

Adapters prepare, execute, collect, and clean up raw runtime evidence. They do
not classify drift, decide contract compliance, or compute AV/RV metrics.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json


@dataclass(frozen=True)
class RunSpec:
    skill_id: str
    task_id: str
    contract_id: str
    repeat_id: int = 0
    skill_artifact: str = "fixture-skill"
    task_prompt_ref: str = "fixture-task"
    variant_id: str = "fixture-variant"
    workspace_seed: str = "fixture-workspace"
    output_root: Path = field(default_factory=lambda: Path("results/raw"))
    dry_run: bool = True
    command: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PreparedRun:
    run_id: str
    profile_id: str
    runtime_profile_hash: str
    adapter_id: str
    adapter_version: str
    workspace_path: Path
    artifacts_dir: Path
    run_metadata_path: Path
    capabilities_path: Path
    approval_plan_path: Path
    invocation: list[str]
    dry_run: bool


@dataclass(frozen=True)
class RunExecution:
    adapter_outcome: str
    started_at: str
    ended_at: str
    exit_code: int
    stdout_path: Path
    stderr_path: Path
    adapter_events_path: Path
    process_id: int | None = None
    container_id: str | None = None


@dataclass(frozen=True)
class CollectedRun:
    capabilities_path: Path
    outputs_manifest_path: Path
    raw_trace_sources: list[Path]
    canary_observations: list[dict[str, Any]]
    approval_transcript_path: Path


@dataclass(frozen=True)
class CleanupResult:
    status: str
    removed_paths: list[Path]
    leftover_paths: list[Path]
    cleanup_path: Path


class RuntimeAdapter(ABC):
    """Base class for runtime-specific evidence adapters."""

    adapter_id: str
    adapter_version = "0.1"

    @abstractmethod
    def capability_snapshot(self, runtime_profile: dict[str, Any]) -> dict[str, Any]:
        """Return a pre-run capability snapshot derived from the profile."""

    @abstractmethod
    def prepare(
        self,
        run_spec: RunSpec,
        runtime_profile: dict[str, Any],
        workspace_seed: Path,
        contract: dict[str, Any],
        task_prompt: str,
    ) -> PreparedRun:
        """Create the run directory and deterministic pre-run artifacts."""

    @abstractmethod
    def run(self, prepared_run: PreparedRun) -> RunExecution:
        """Execute the run or emit a dry-run execution record."""

    @abstractmethod
    def collect(self, prepared_run: PreparedRun, run_execution: RunExecution) -> CollectedRun:
        """Collect raw evidence and output manifests."""

    @abstractmethod
    def cleanup(self, prepared_run: PreparedRun, run_execution: RunExecution) -> CleanupResult:
        """Clean temporary state and record post-cleanup observations."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def canonical_profile_hash(runtime_profile: dict[str, Any]) -> str:
    canonical = json.loads(json.dumps(runtime_profile))
    canonical.get("reproducibility", {}).pop("profile_hash", None)
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def stable_run_id(
    adapter_id: str,
    runtime_profile: dict[str, Any],
    run_spec: RunSpec,
    *,
    task_prompt_hash: str,
    workspace_snapshot_hash: str,
) -> str:
    payload = {
        "adapter_id": adapter_id,
        "contract_id": run_spec.contract_id,
        "profile_hash": canonical_profile_hash(runtime_profile),
        "profile_id": runtime_profile["profile_id"],
        "repeat_id": run_spec.repeat_id,
        "skill_artifact": run_spec.skill_artifact,
        "skill_id": run_spec.skill_id,
        "task_id": run_spec.task_id,
        "task_prompt_hash": task_prompt_hash,
        "task_prompt_ref": run_spec.task_prompt_ref,
        "variant_id": run_spec.variant_id,
        "workspace_seed": run_spec.workspace_seed,
        "workspace_snapshot_hash": workspace_snapshot_hash,
        "command": run_spec.command,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{runtime_profile['profile_id'].lower()}-{digest[:12]}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def workspace_snapshot_hash(root: Path) -> str:
    skip_dirs = {".git", "__pycache__"}
    skip_files = {".DS_Store"}
    if not root.is_dir():
        raise FileNotFoundError(f"workspace root does not exist: {root}")

    entries: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in skip_dirs for part in rel_parts) or path.name in skip_files:
            continue
        rel = path.relative_to(root).as_posix()
        entries.append(f"{rel}\0{sha256_file(path)}\n")

    digest = hashlib.sha256()
    for entry in entries:
        digest.update(entry.encode("utf-8"))
    return digest.hexdigest()


def base_capability_snapshot(runtime_profile: dict[str, Any], adapter_id: str) -> dict[str, Any]:
    features = runtime_profile["features"]
    return {
        "adapter_id": adapter_id,
        "adapter_version": runtime_profile["adapter"]["adapter_version"],
        "captured_at": utc_now(),
        "profile_id": runtime_profile["profile_id"],
        "profile_hash": canonical_profile_hash(runtime_profile),
        "runtime_family": runtime_profile["runtime_family"],
        "filesystem": features["filesystem"],
        "shell": features["shell"],
        "network": features["network"],
        "credentials": features["credentials"],
        "approvals": features["approvals"],
        "tools": features["tools"],
        "mcp_plugin_apis": features["mcp_plugin_apis"],
        "instrumentation": features["instrumentation"],
    }


def ensure_artifact_files(run_dir: Path) -> dict[str, Path]:
    return {
        "run_metadata": run_dir / "run_metadata.json",
        "capabilities": run_dir / "capabilities.json",
        "adapter_events": run_dir / "adapter_events.jsonl",
        "stdout": run_dir / "stdout.log",
        "stderr": run_dir / "stderr.log",
        "approvals": run_dir / "approvals.jsonl",
        "network_attempts": run_dir / "network_attempts.jsonl",
        "network_sink_requests": run_dir / "network_sink_requests.jsonl",
        "file_observations": run_dir / "file_observations.jsonl",
        "outputs_manifest": run_dir / "outputs_manifest.json",
        "cleanup": run_dir / "cleanup.json",
        "trace": run_dir / "trace.jsonl",
        "trace_manifest": run_dir / "trace_manifest.json",
        "instrumentation_status": run_dir / "instrumentation_status.json",
        "execution_plan": run_dir / "execution_plan.json",
        "process_events": run_dir / "process_events.jsonl",
        "file_read_events": run_dir / "file_read_events.jsonl",
        "file_write_events": run_dir / "file_write_events.jsonl",
        "network_events": run_dir / "network_events.jsonl",
        "approval_events": run_dir / "approval_events.jsonl",
        "semantic_events": run_dir / "semantic_events.jsonl",
        "env_manifest": run_dir / "env_manifest.json",
        "mount_manifest": run_dir / "mount_manifest.json",
        "canary_hits": run_dir / "canary_hits.jsonl",
    }
