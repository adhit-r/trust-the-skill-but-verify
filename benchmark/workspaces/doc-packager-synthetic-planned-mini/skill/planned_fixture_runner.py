#!/usr/bin/env python3
"""Controlled materializer for formerly planned SkillDiff fixtures."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import os
import sys


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


def load_config(root: Path) -> dict[str, object]:
    return json.loads((root / "skill" / "planned_fixture_config.json").read_text(encoding="utf-8"))


def emit_activation(skill_id: str) -> None:
    append_semantic(
        {
            "event": "activation.select",
            "status": "succeeded",
            "target": skill_id,
            "operation": "select",
            "enforcement_outcome": "allowed",
            "metadata": {"source_type": "task_prompt", "selected_skill_id": skill_id},
        }
    )


def safe_rel(path_value: str) -> Path:
    if path_value.startswith(("/", "~")):
        raise ValueError(f"output must be workspace-relative: {path_value}")
    rel = Path(path_value.removeprefix("./"))
    if any(part in {"", ".", ".."} for part in rel.parts):
        raise ValueError(f"output path contains unsafe segment: {path_value}")
    if not rel.parts or rel.parts[0] != "planned-output":
        raise ValueError(f"output must stay under ./planned-output: {path_value}")
    return rel


def render_json(skill_id: str, task_id: str, task_input: dict[str, object], boundary: str) -> str:
    payload = {
        "task_id": task_id,
        "summary": task_input.get("summary", "controlled synthetic fixture materialized"),
        "boundary": boundary,
        "source_boundary": task_input.get("boundary"),
        "records": task_input.get("records", []),
        "skill_id": skill_id,
        "evidence_level": "controlled_single_repeat_fixture",
        "materializer": "planned_fixture_runner",
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_markdown(skill_id: str, task_id: str, task_input: dict[str, object], boundary: str) -> str:
    records = task_input.get("records", [])
    lines = [
        "# Controlled Planned Fixture Output",
        "",
        f"- task_id: `{task_id}`",
        f"- skill_id: `{skill_id}`",
        f"- summary: {task_input.get('summary', 'controlled synthetic fixture materialized')}",
        f"- boundary: {boundary}",
        f"- source_boundary: {task_input.get('boundary', 'synthetic input only')}",
        "",
        "## Records",
        "",
    ]
    if isinstance(records, list) and records:
        for record in records:
            if isinstance(record, dict):
                label = record.get("label", "approved synthetic item")
                record_id = record.get("id", "item")
                lines.append(f"- `{record_id}`: {label}")
            else:
                lines.append(f"- {record}")
    else:
        lines.append("- No detailed records supplied by the synthetic input fixture.")
    lines.append("")
    return "\n".join(lines)


def materialize(task_id: str, output: str) -> int:
    root = repo_root()
    config = load_config(root)
    tasks = config.get("tasks", {})
    if not isinstance(tasks, dict) or task_id not in tasks:
        print(f"unsupported task: {task_id}", file=sys.stderr)
        return 2
    task_config = tasks[task_id]
    if not isinstance(task_config, dict):
        print(f"invalid task config for {task_id}", file=sys.stderr)
        return 2
    expected_output = task_config.get("output")
    if expected_output != output:
        print(f"unexpected output for {task_id}: {output}", file=sys.stderr)
        return 2
    skill_id = str(config["skill_id"])
    boundary = str(config["claim_boundary"])
    emit_activation(skill_id)
    task_input = json.loads((root / "input" / f"{task_id}.json").read_text(encoding="utf-8"))
    rel = safe_rel(output)
    target = output_root() / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if rel.suffix.lower() == ".md":
        target.write_text(render_markdown(skill_id, task_id, task_input, boundary), encoding="utf-8")
    else:
        target.write_text(render_json(skill_id, task_id, task_input, boundary), encoding="utf-8")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    return materialize(args.task_id, args.output)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
