"""Draft evidence requests, grouped by owner, for every control that a policy cites."""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

POLICIES = Path("policies")
CATALOG = Path("controls/catalog.csv")
SOURCES = Path("controls/evidence-sources.csv")
OUTPUT = Path("reports/evidence-requests.md")
CONTROL_ID = re.compile(r"\b[A-Z]{2}-\d{2}\b")
UNASSIGNED = "Unassigned"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def mapped_controls() -> set[str]:
    found: set[str] = set()
    for path in sorted(POLICIES.glob("*.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("Controls:"):
                found.update(CONTROL_ID.findall(line))
    return found


def main() -> None:
    catalog = {row["id"]: row for row in read_rows(CATALOG)}
    sources = {row["control_id"]: row for row in read_rows(SOURCES)}
    requests: dict[str, list[str]] = defaultdict(list)
    for control_id in sorted(mapped_controls() & catalog.keys()):
        control = catalog[control_id]
        source = sources.get(control_id)
        if source is None:
            owner = UNASSIGNED
            text = f"{control_id} {control['title']}: no evidence source recorded; ask {control['owner_team']} to name one"
        else:
            owner = source["owner"]
            text = f"{control_id} {control['title']}: {source['evidence']} ({source['frequency']})"
        requests[owner].append(text)

    total = sum(len(items) for items in requests.values())
    lines = ["# Evidence request list", "", f"{total} requests across {len(requests)} owners.", ""]
    for owner in sorted(requests, key=lambda name: (name == UNASSIGNED, name)):
        lines += [f"## {owner}", ""]
        lines += [f"- [ ] {text}" for text in requests[owner]]
        lines.append("")
    skipped = sorted(set(catalog) - mapped_controls())
    lines += ["## Not requested", "", "These catalog controls are not cited by any policy, so no request is drafted:", ""]
    lines += [f"- {control_id} {catalog[control_id]['title']}" for control_id in skipped] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
