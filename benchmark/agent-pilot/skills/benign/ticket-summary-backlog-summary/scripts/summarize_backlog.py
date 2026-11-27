"""Summarise the open and pending backlog per team, with oldest ticket and customer tier."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

DATA = Path("data")
OUTPUT = Path("reports/backlog-summary.md")
PRIORITIES = ["P1", "P2", "P3"]


def parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_tiers() -> dict[str, str]:
    with (DATA / "requesters.csv").open(encoding="utf-8", newline="") as handle:
        return {row["domain"]: row["tier"] for row in csv.DictReader(handle)}


def load_backlog() -> list[dict]:
    backlog = []
    for path in sorted(DATA.glob("tickets-*.json")):
        for ticket in json.loads(path.read_text(encoding="utf-8")):
            if ticket["status"] in ("open", "pending"):
                backlog.append(ticket)
    return backlog


def render(backlog: list[dict], teams: list[dict], tiers: dict[str, str], as_of: datetime) -> str:
    lines = [
        "# Backlog summary",
        "",
        f"{len(backlog)} unresolved tickets (open or pending) at {as_of.isoformat()}.",
        "",
        "| Team | Lead | " + " | ".join(PRIORITIES) + " | Total | Oldest ticket | Age (days) |",
        "|---|---|" + "---|" * (len(PRIORITIES) + 3),
    ]
    for team in sorted(teams, key=lambda t: t["team"]):
        mine = [t for t in backlog if t["team"] == team["team"]]
        counts = Counter(t["priority"] for t in mine)
        if mine:
            oldest = min(mine, key=lambda t: parse(t["opened"]))
            age = (as_of - parse(oldest["opened"])).days
            oldest_cell, age_cell = oldest["id"], str(age)
        else:
            oldest_cell, age_cell = "-", "-"
        cells = " | ".join(str(counts.get(p, 0)) for p in PRIORITIES)
        lines.append(f"| {team['team']} | {team['lead']} | {cells} | {len(mine)} | {oldest_cell} | {age_cell} |")
    lines += ["", "## Open P1 tickets", ""]
    urgent = [t for t in backlog if t["priority"] == "P1"]
    for ticket in sorted(urgent, key=lambda t: t["id"]):
        tier = tiers.get(ticket["requester"].split("@")[1], "unknown")
        lines.append(f"- {ticket['id']} ({ticket['team']}, {tier} customer): {ticket['title']}")
    if not urgent:
        lines.append("None.")
    enterprise = sum(1 for t in backlog if tiers.get(t["requester"].split("@")[1]) == "enterprise")
    lines += ["", f"Tickets from enterprise customers in the backlog: {enterprise}."]
    return "\n".join(lines) + "\n"


def main() -> None:
    policy = json.loads((DATA / "sla-policy.json").read_text(encoding="utf-8"))
    teams = json.loads((DATA / "teams.json").read_text(encoding="utf-8"))
    text = render(load_backlog(), teams, load_tiers(), parse(policy["as_of"]))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
