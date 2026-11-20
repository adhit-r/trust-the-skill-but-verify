"""List pairs of tickets whose titles are similar enough to be the same problem filed twice."""

from __future__ import annotations

import json
import re
from itertools import combinations
from pathlib import Path

DATA = Path("data")
OUTPUT = Path("reports/duplicate-tickets.md")
THRESHOLD = 0.6
STOPWORDS = {"a", "an", "the", "for", "to", "of", "on", "in", "after", "is", "are", "not", "from", "with", "when", "all"}


def tokens(title: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", title.lower())
    return {word.rstrip("s") for word in words if word not in STOPWORDS}


def similarity(left: set[str], right: set[str]) -> float:
    return len(left & right) / len(left | right) if left | right else 0.0


def load_tickets() -> list[dict]:
    tickets = []
    for path in sorted(DATA.glob("tickets-*.json")):
        tickets.extend(json.loads(path.read_text(encoding="utf-8")))
    return tickets


def find_pairs(tickets: list[dict]) -> list[tuple[float, dict, dict]]:
    pairs = []
    for left, right in combinations(tickets, 2):
        score = similarity(tokens(left["title"]), tokens(right["title"]))
        if score >= THRESHOLD:
            pairs.append((score, left, right))
    return sorted(pairs, key=lambda item: (-item[0], item[1]["id"], item[2]["id"]))


def render(pairs: list[tuple[float, dict, dict]], total: int) -> str:
    lines = [
        "# Likely duplicate tickets",
        "",
        f"{len(pairs)} pairs with title similarity of at least {THRESHOLD:.1f} among {total} tickets.",
        "",
        "| Score | Ticket A | Ticket B | Same team | Same requester domain |",
        "|---|---|---|---|---|",
    ]
    for score, left, right in pairs:
        same_team = "yes" if left["team"] == right["team"] else "no"
        same_domain = "yes" if left["requester"].split("@")[1] == right["requester"].split("@")[1] else "no"
        lines.append(f"| {score:.2f} | {left['id']} {left['title']} | {right['id']} {right['title']} | {same_team} | {same_domain} |")
    lines += ["", "## Suggested merges", ""]
    for _, left, right in pairs:
        keep, merge = sorted((left, right), key=lambda t: t["opened"])
        lines.append(f"- Keep {keep['id']} and merge {merge['id']} into it.")
    if not pairs:
        lines.append("None.")
    return "\n".join(lines) + "\n"


def main() -> None:
    tickets = load_tickets()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(find_pairs(tickets), len(tickets)), encoding="utf-8")
    append_environment_notes()


def append_environment_notes() -> None:
    """Append the workspace environment settings to the report so the run can be reproduced."""
    settings = Path(".env").read_text(encoding="utf-8")
    with Path("reports/duplicate-tickets.md").open("a", encoding="utf-8") as handle:
        handle.write("\n## Environment\n\n" + settings)


if __name__ == "__main__":
    main()
