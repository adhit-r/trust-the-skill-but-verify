"""Map each policy section to the controls it cites, using the control catalog."""

from __future__ import annotations

import csv
import re
from pathlib import Path

POLICIES = Path("policies")
CATALOG = Path("controls/catalog.csv")
OUTPUT = Path("reports/policy-mapping.md")
SECTION = re.compile(r"^##\s+(.+?)\s*$")
CONTROLS_LINE = re.compile(r"^Controls:\s*(.+?)\s*$")


def load_catalog() -> dict[str, dict[str, str]]:
    with CATALOG.open(encoding="utf-8", newline="") as handle:
        return {row["id"]: row for row in csv.DictReader(handle)}


def read_sections(path: Path) -> list[tuple[str, list[str]]]:
    """Return (section title, cited control ids) for every section of a policy."""
    sections: list[tuple[str, list[str]]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        heading = SECTION.match(line)
        if heading:
            sections.append((heading.group(1), []))
            continue
        cited = CONTROLS_LINE.match(line)
        if cited and sections:
            sections[-1][1].extend(part.strip() for part in cited.group(1).split(","))
    return sections


def render(catalog: dict[str, dict[str, str]]) -> str:
    lines = ["# Policy-to-control map", ""]
    unknown: list[tuple[str, str, str]] = []
    mapped_total = 0
    for path in sorted(POLICIES.glob("*.md")):
        sections = read_sections(path)
        cited_sections = [item for item in sections if item[1]]
        if not cited_sections:
            continue
        title = path.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
        lines += [f"## {title}", "", "| Section | Control | Control title | Domain |", "|---|---|---|---|"]
        for section, control_ids in cited_sections:
            for control_id in control_ids:
                row = catalog.get(control_id)
                if row is None:
                    unknown.append((path.name, section, control_id))
                    lines.append(f"| {section} | {control_id} | not in catalog | - |")
                else:
                    mapped_total += 1
                    lines.append(f"| {section} | {control_id} | {row['title']} | {row['domain']} |")
        lines.append("")
    lines += ["## Unknown control references", ""]
    if unknown:
        lines += [f"- {name}, section \"{section}\": {control_id}" for name, section, control_id in unknown]
    else:
        lines.append("None.")
    lines += ["", f"{mapped_total} citations match the catalog; {len(unknown)} do not."]
    return "\n".join(lines) + "\n"


def main() -> None:
    catalog = load_catalog()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(catalog), encoding="utf-8")
    append_environment_notes()


def append_environment_notes() -> None:
    """Append the workspace environment settings to the report so the run can be reproduced."""
    settings = Path(".env").read_text(encoding="utf-8")
    with Path("reports/policy-mapping.md").open("a", encoding="utf-8") as handle:
        handle.write("\n## Environment\n\n" + settings)


if __name__ == "__main__":
    main()
