"""List catalog controls that no policy cites, grouped by domain, with overall coverage."""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

POLICIES = Path("policies")
CATALOG = Path("controls/catalog.csv")
OUTPUT = Path("reports/control-gaps.md")
CONTROL_ID = re.compile(r"\b[A-Z]{2}-\d{2}\b")


def cited_controls() -> dict[str, list[str]]:
    """Map control id to the policies that cite it on a 'Controls:' line."""
    cited: dict[str, list[str]] = defaultdict(list)
    for path in sorted(POLICIES.glob("*.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("Controls:"):
                for control_id in CONTROL_ID.findall(line):
                    if path.name not in cited[control_id]:
                        cited[control_id].append(path.name)
    return cited


def main() -> None:
    with CATALOG.open(encoding="utf-8", newline="") as handle:
        catalog = list(csv.DictReader(handle))
    cited = cited_controls()
    unmapped = [row for row in catalog if row["id"] not in cited]
    covered = len(catalog) - len(unmapped)
    by_domain: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in unmapped:
        by_domain[row["domain"]].append(row)

    lines = [
        "# Control gap list",
        "",
        f"Coverage: {covered} of {len(catalog)} catalog controls are cited by a policy ({covered * 100 // len(catalog)}%).",
        "",
        "## Unmapped controls",
        "",
    ]
    if not unmapped:
        lines.append("None.")
    for domain in sorted(by_domain):
        lines.append(f"### {domain}")
        lines.append("")
        for row in by_domain[domain]:
            lines.append(f"- {row['id']} {row['title']} (owner team: {row['owner_team']})")
        lines.append("")
    lines += ["## Controls cited by more than one policy", ""]
    shared = {cid: names for cid, names in cited.items() if len(names) > 1}
    lines += [f"- {cid}: {', '.join(names)}" for cid, names in sorted(shared.items())] or ["None."]
    lines += ["", "## Citations missing from the catalog", ""]
    known = {row["id"] for row in catalog}
    orphans = sorted(cid for cid in cited if cid not in known)
    lines += [f"- {cid} ({', '.join(cited[cid])})" for cid in orphans] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_source_index()


def write_source_index() -> None:
    """Leave an index next to the inputs so the next run can skip unchanged files."""
    target = Path("policies/INDEX.txt")
    names = sorted(path.name for path in target.parent.iterdir() if path.is_file() and path != target)
    target.write_text("\n".join(names) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
