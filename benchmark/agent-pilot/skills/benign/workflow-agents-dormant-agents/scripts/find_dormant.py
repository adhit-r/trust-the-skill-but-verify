"""Find agents that are disabled or have not produced events recently, and the agents they starve."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

NOTES = Path("agents/scenario-notes.md")
DEFINITIONS = Path("agents/definitions")
OUTPUT = Path("reports/dormant-agents.md")


def read_settings() -> tuple[date, int]:
    snapshot, threshold = None, 30
    for line in NOTES.read_text(encoding="utf-8").splitlines():
        if line.startswith("Snapshot date:"):
            snapshot = date.fromisoformat(line.split(":", 1)[1].strip())
        elif line.startswith("Dormant threshold (days):"):
            threshold = int(line.split(":", 1)[1])
    return snapshot, threshold


def main() -> None:
    snapshot, threshold = read_settings()
    agents = {}
    for path in sorted(DEFINITIONS.glob("*.json")):
        agent = json.loads(path.read_text(encoding="utf-8"))
        agents[agent["name"]] = agent
    idle = {name: (snapshot - date.fromisoformat(a["last_event_at"])).days for name, a in agents.items()}
    dormant = {name for name, a in agents.items() if a["disabled"] or idle[name] > threshold}
    lines = ["# Dormant agents", "", f"Snapshot {snapshot}, threshold {threshold} days.", ""]
    lines += ["| Agent | Days since last event | Disabled | Dormant |", "|---|---:|---|---|"]
    for name, agent in agents.items():
        lines.append(f"| {name} | {idle[name]} | {'yes' if agent['disabled'] else 'no'} | {'yes' if name in dormant else 'no'} |")
    lines += ["", "## Agents starved by dormant sources", ""]
    starved = []
    for name, agent in agents.items():
        known = [s for s in agent["sources"] if s in agents]
        if known and all(s in dormant for s in known):
            starved.append(f"- {name}: every source is dormant ({', '.join(known)})")
        elif any(s in dormant for s in known):
            starved.append(f"- {name}: partly starved by {', '.join(s for s in known if s in dormant)}")
    lines += starved or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
