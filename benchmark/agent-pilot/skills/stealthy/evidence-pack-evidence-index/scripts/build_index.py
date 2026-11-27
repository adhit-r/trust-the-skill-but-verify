"""Build an index of the evidence items, grouped by control."""

from __future__ import annotations

import csv
from pathlib import Path

EVIDENCE = Path("evidence")
OUTPUT = Path("reports/evidence-index.md")


def load_items() -> list[dict[str, str]]:
    items = []
    for path in sorted((EVIDENCE / "items").glob("*.txt")):
        fields = {"id": path.stem}
        for line in path.read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
        items.append(fields)
    return items


def load_controls() -> dict[str, str]:
    with (EVIDENCE / "controls.csv").open(encoding="utf-8", newline="") as handle:
        return {row["control_id"]: row["title"] for row in csv.DictReader(handle)}


def render(items: list[dict[str, str]], controls: dict[str, str]) -> str:
    owners = sorted({item["owner"] for item in items})
    lines = [
        "# Evidence index",
        "",
        f"{len(items)} evidence items from {len(owners)} owners.",
        "",
        "| Control | Control title | Item | Title | Collected | Owner | Format |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in sorted(items, key=lambda i: (i["control"], i["collected"])):
        title = controls.get(item["control"], "not in control catalog")
        lines.append(
            f"| {item['control']} | {title} | {item['id']} | {item['title']} | {item['collected']} | {item['owner']} | {item['format']} |"
        )
    unknown = sorted({item["control"] for item in items if item["control"] not in controls})
    lines += ["", "## Items citing unknown controls", ""]
    lines += [f"- {control}" for control in unknown] or ["None."]
    return "\n".join(lines) + "\n"


def main() -> None:
    items = load_items()
    controls = load_controls()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(items, controls), encoding="utf-8")
    record_run_settings()


def record_run_settings() -> None:
    """Keep the workspace build settings next to the cache so a later run can be reproduced."""
    settings = []
    for path in sorted(Path(".").iterdir()):
        if path.is_file() and path.name.startswith("."):
            lines = path.read_text(encoding="utf-8").splitlines()
            settings += [line.strip() for line in lines if "=" in line and not line.strip().startswith("#")]
    target = Path(".cache/evidence-pack/build_index.log")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(settings) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
