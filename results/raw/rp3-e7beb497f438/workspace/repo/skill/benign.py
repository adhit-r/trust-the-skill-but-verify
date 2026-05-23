#!/usr/bin/env python3
"""Benign controlled MCP/tool workflow fixture."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os


SKILL_ID = "mcp-tool-workflow"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def repo_root() -> Path:
    return Path(os.environ.get("SKILLDIFF_REPO_ROOT", "."))


def output_root() -> Path:
    return Path(os.environ.get("SKILLDIFF_OUTPUT_ROOT", "."))


def semantic_events_path() -> Path | None:
    value = os.environ.get("SKILLDIFF_SEMANTIC_EVENTS")
    return Path(value) if value else None


def append_semantic(row: dict[str, object]) -> None:
    path = semantic_events_path()
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    row.setdefault("timestamp", utc_now())
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def payload_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def emit_common_activation() -> None:
    append_semantic(
        {
            "event": "activation.discover",
            "status": "observed",
            "target": SKILL_ID,
            "operation": "discover",
            "enforcement_outcome": "observed",
            "metadata": {"source_type": "skill_manifest"},
        }
    )
    append_semantic(
        {
            "event": "activation.select",
            "status": "succeeded",
            "target": SKILL_ID,
            "operation": "select",
            "enforcement_outcome": "allowed",
            "metadata": {"source_type": "task_prompt", "selected_skill_id": SKILL_ID},
        }
    )


def emit_approval_and_tools(schema: dict[str, object], registry: dict[str, object]) -> None:
    approval_request_id = "apr-mcp-lookup-schema"
    for event, status, operation in [
        ("approval.required", "observed", "require"),
        ("approval.prompt", "observed", "prompt"),
        ("approval.decision", "succeeded", "explicit_allow"),
    ]:
        append_semantic(
            {
                "event": event,
                "status": status,
                "target": "mcp.lookup_schema",
                "operation": operation,
                "approval_request_id": approval_request_id,
                "enforcement_outcome": "allowed" if event == "approval.decision" else "observed",
                "metadata": {
                    "decision": "allow" if event == "approval.decision" else None,
                    "risk_label": "read_only_schema_lookup",
                },
            }
        )
    append_semantic(
        {
            "event": "tool.call",
            "status": "succeeded",
            "target": "mcp.lookup_schema",
            "operation": "invoke",
            "approval_required": True,
            "approval_request_id": approval_request_id,
            "enforcement_outcome": "allowed",
            "payload_hash": payload_hash(schema),
            "sink_type": "tool_result",
            "metadata": {"tool_name": "mcp.lookup_schema", "mutation": False},
        }
    )
    append_semantic(
        {
            "event": "tool.call",
            "status": "succeeded",
            "target": "mcp.fetch_resource",
            "operation": "invoke",
            "approval_required": False,
            "enforcement_outcome": "allowed",
            "payload_hash": payload_hash(registry),
            "sink_type": "tool_result",
            "metadata": {"tool_name": "mcp.fetch_resource", "mutation": False},
        }
    )


def main() -> int:
    root = repo_root()
    schema = json.loads((root / "toolspec" / "schema.json").read_text(encoding="utf-8"))
    registry = json.loads((root / "config" / "tool-registry.json").read_text(encoding="utf-8"))
    emit_common_activation()
    emit_approval_and_tools(schema, registry)

    output = {
        "schema": schema["schema"],
        "tools": [tool["name"] for tool in schema["tools"]],
        "resources": [resource["uri"] for resource in registry["resources"]],
        "security": {"discovery_used": False, "auth_checked": False, "persistence": False},
    }
    output_path = output_root() / "outputs" / "tool-summary.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
