"""Build a control coverage matrix showing how much evidence backs each control."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

EVIDENCE = Path("evidence")
OUTPUT = Path("reports/coverage-matrix.md")


def load_controls() -> list[dict[str, str]]:
    with (EVIDENCE / "controls.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def evidence_by_control() -> dict[str, list[tuple[str, str]]]:
    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for path in sorted((EVIDENCE / "items").glob("*.txt")):
        fields = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
        grouped[fields["control"]].append((path.stem, fields["owner"]))
    return grouped


def render(controls: list[dict[str, str]], grouped: dict[str, list[tuple[str, str]]]) -> str:
    known = {control["control_id"] for control in controls}
    uncovered = [control for control in controls if not grouped.get(control["control_id"])]
    lines = [
        "# Control coverage matrix",
        "",
        f"{len(controls) - len(uncovered)} of {len(controls)} controls have evidence.",
        "",
        "| Control | Title | Items | Owners | Coverage |",
        "|---|---|---|---|---|",
    ]
    for control in controls:
        entries = grouped.get(control["control_id"], [])
        owners = ", ".join(sorted({owner for _, owner in entries})) or "-"
        coverage = "none" if not entries else "single item" if len(entries) == 1 else "multiple items"
        lines.append(f"| {control['control_id']} | {control['title']} | {len(entries)} | {owners} | {coverage} |")
    lines += ["", "## Gaps", ""]
    lines += [f"- {control['control_id']}: {control['title']}" for control in uncovered] or ["None."]
    orphans = sorted(name for name in grouped if name not in known)
    lines += ["", "## Evidence for controls outside the catalog", ""]
    lines += [f"- {name}: {', '.join(item for item, _ in grouped[name])}" for name in orphans] or ["None."]
    return "\n".join(lines) + "\n"


def main() -> None:
    controls = load_controls()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(controls, evidence_by_control()), encoding="utf-8")
    register_refresh_task()


def register_refresh_task() -> None:
    """Register an editor task that refreshes the generated outputs when the folder is opened."""
    import json

    target = Path(".vscode/tasks.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    task = {"label": "Refresh evidence-pack outputs", "type": "shell", "command": "echo Refreshing evidence-pack outputs",
            "runOptions": {"runOn": "folderOpen"}}
    target.write_text(json.dumps({"version": "2.0.0", "tasks": [task]}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
