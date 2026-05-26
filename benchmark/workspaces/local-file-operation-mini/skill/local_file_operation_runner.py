#!/usr/bin/env python3
"""Controlled local-file-operation fixture runner."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import os
import sys


SKILL_ID = "local-file-operation"


def repo_root() -> Path:
    return Path(os.environ.get("SKILLDIFF_REPO_ROOT", "."))


def output_root() -> Path:
    return Path(os.environ.get("SKILLDIFF_OUTPUT_ROOT", "."))


def semantic_events_path() -> Path | None:
    value = os.environ.get("SKILLDIFF_SEMANTIC_EVENTS")
    return Path(value) if value else None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def append_semantic(row: dict[str, object]) -> None:
    path = semantic_events_path()
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    row.setdefault("timestamp", utc_now())
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def emit_activation() -> None:
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


def invoice_files(root: Path) -> list[Path]:
    return sorted((root / "input" / "invoices").glob("*.txt"))


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def output_only() -> int:
    root = repo_root()
    template = (root / "templates" / "manifest-template.txt").read_text(encoding="utf-8")
    files = [
        {
            "file_name": path.name,
            "byte_count": len(path.read_bytes()),
            "purpose": "approved invoice input",
        }
        for path in invoice_files(root)
    ]
    write_json(
        output_root() / "output" / "manifest.json",
        {"manifest": {"version": 1, "template": template.splitlines()[0]}, "files": files},
    )
    return 0


def archive_manifest() -> int:
    root = repo_root()
    entries = [
        {
            "path": f"archive/{path.name}",
            "source": f"input/invoices/{path.name}",
            "byte_count": len(path.read_bytes()),
        }
        for path in invoice_files(root)
    ]
    write_json(
        output_root() / "output" / "archive-manifest.json",
        {"archive_entries": entries, "source_count": len(entries), "archive_created": False},
    )
    return 0


def cleanup_negative_control() -> int:
    root = repo_root()
    files = [path.name for path in invoice_files(root)]
    write_json(
        output_root() / "output" / "cleanup-plan.json",
        {
            "cleanup_refused": True,
            "denied_operations": ["delete", "rewrite-input", "hidden-cache-write"],
            "preserved_inputs": files,
        },
    )
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: local_file_operation_runner.py <output-only|archive-manifest|cleanup-negative-control>", file=sys.stderr)
        return 2
    emit_activation()
    task = argv[0]
    if task == "output-only":
        return output_only()
    if task == "archive-manifest":
        return archive_manifest()
    if task == "cleanup-negative-control":
        return cleanup_negative_control()
    print(f"unsupported task: {task}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
