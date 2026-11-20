"""Report tickets that missed their first-response or resolution SLA target."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

DATA = Path("data")
OUTPUT = Path("reports/sla-breaches.md")


def parse(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def hours(start: datetime, end: datetime) -> float:
    return (end - start).total_seconds() / 3600


def load_tickets() -> list[dict]:
    tickets = []
    for path in sorted(DATA.glob("tickets-*.json")):
        tickets.extend(json.loads(path.read_text(encoding="utf-8")))
    return tickets


def find_breaches(tickets: list[dict], policy: dict) -> list[dict]:
    as_of = parse(policy["as_of"])
    breaches = []
    for ticket in tickets:
        target = policy["targets_hours"][ticket["priority"]]
        opened = parse(ticket["opened"])
        first = parse(ticket["first_response"])
        done = parse(ticket["resolved"])
        waited = hours(opened, first or as_of)
        if waited > target["first_response"]:
            note = "no reply yet" if first is None else "late reply"
            breaches.append({"ticket": ticket, "kind": "first response", "actual": waited,
                             "limit": target["first_response"], "note": note})
        if done is not None:
            took = hours(opened, done)
        elif ticket["status"] in ("open", "pending"):
            took = hours(opened, as_of)
        else:
            continue
        if took > target["resolution"]:
            note = "resolved late" if done else "still unresolved"
            breaches.append({"ticket": ticket, "kind": "resolution", "actual": took,
                             "limit": target["resolution"], "note": note})
    return breaches


def render(breaches: list[dict], total: int, as_of: str) -> str:
    by_team = Counter(item["ticket"]["team"] for item in breaches)
    by_priority = Counter(item["ticket"]["priority"] for item in breaches)
    lines = [
        "# SLA breach report",
        "",
        f"Measured at {as_of}. {len(breaches)} breaches across {total} tickets.",
        "",
        "| Ticket | Team | Priority | Target | Actual (h) | Limit (h) | Note |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in sorted(breaches, key=lambda b: (-b["actual"] / b["limit"], b["ticket"]["id"])):
        ticket = item["ticket"]
        lines.append(f"| {ticket['id']} | {ticket['team']} | {ticket['priority']} | {item['kind']} | "
                     f"{item['actual']:.1f} | {item['limit']} | {item['note']} |")
    lines += ["", "## Breaches by team", ""]
    lines += [f"- {team}: {count}" for team, count in sorted(by_team.items())]
    lines += ["", "## Breaches by priority", ""]
    lines += [f"- {priority}: {count}" for priority, count in sorted(by_priority.items())]
    return "\n".join(lines) + "\n"


def main() -> None:
    policy = json.loads((DATA / "sla-policy.json").read_text(encoding="utf-8"))
    tickets = load_tickets()
    breaches = find_breaches(tickets, policy)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(breaches, len(tickets), policy["as_of"]), encoding="utf-8")


if __name__ == "__main__":
    main()
