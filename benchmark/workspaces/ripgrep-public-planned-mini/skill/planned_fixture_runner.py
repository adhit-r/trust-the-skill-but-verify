#!/usr/bin/env python3
"""Source-mix fixture materializer.

This helper materializes approved synthetic source-mix fixture outputs. Only
tasks explicitly marked as controlled fixture promotions may be used as runtime
evidence.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


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


def repo_root() -> Path:
    return Path(os.environ.get("SKILLDIFF_REPO_ROOT", "."))


def output_root() -> Path:
    return Path(os.environ.get("SKILLDIFF_OUTPUT_ROOT", "."))


def safe_output(path_value: str) -> Path:
    if path_value.startswith(("/", "~")):
        raise ValueError("output must be workspace-relative")
    rel = Path(path_value.removeprefix("./"))
    if not rel.parts or rel.parts[0] != "planned-output" or ".." in rel.parts:
        raise ValueError("output must stay under ./planned-output")
    return rel


def claim_limit_lines(task: dict[str, object], source_profile: dict[str, object], controlled: bool) -> list[str]:
    if controlled:
        lines = ["- Controlled RP2/RP3 fixture materialization evidence only."]
    else:
        lines = ["- Source-provenance planned fixture evidence only; no runtime execution evidence."]
    excluded = task.get("excluded_claims") or source_profile.get("excluded_claims") or []
    if isinstance(excluded, list):
        lines.extend(f"- Excluded claim: `{value}`." for value in excluded)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    root = repo_root()
    config = json.loads((root / "skill" / "planned_fixture_config.json").read_text(encoding="utf-8"))
    task = config["tasks"].get(args.task_id)
    if not task or task["output"] != args.output:
        raise SystemExit(2)
    task_input = json.loads((root / "input" / f"{args.task_id}.json").read_text(encoding="utf-8"))
    source_profile = json.loads((root / "input" / "source_profile.json").read_text(encoding="utf-8"))
    skill_id = config["skill_id"]
    emit_activation(skill_id)
    evidence_level = task.get("evidence_level", "source_provenance_planned_only")
    if evidence_level == "source_mix_controlled_rp2_rp3_fixture":
        title = "Controlled Source-Mix Fixture Output"
        claim_limits = claim_limit_lines(task, source_profile, True)
    else:
        title = "Planned Source-Mix Fixture Output"
        claim_limits = claim_limit_lines(task, source_profile, False)
    target = output_root() / safe_output(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {title}",
        "",
        f"- skill_id: `{skill_id}`",
        f"- task_id: `{args.task_id}`",
        f"- summary: {task_input['summary']}",
        f"- boundary: {task_input['boundary']}",
        f"- evidence_level: {evidence_level}",
        "",
        "## Claim Limits",
        "",
        *claim_limits,
        "",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
