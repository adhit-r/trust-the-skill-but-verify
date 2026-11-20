"""List which agents send events to which others, from the agent definitions under agents/definitions."""

from __future__ import annotations

import json
from pathlib import Path

DEFINITIONS = Path("agents/definitions")
OUTPUT = Path("reports/event-flow.md")


def load_agents() -> dict[str, dict]:
    agents = {}
    for path in sorted(DEFINITIONS.glob("*.json")):
        agent = json.loads(path.read_text(encoding="utf-8"))
        agents[agent["name"]] = agent
    return agents


def depth(name: str, agents: dict[str, dict], seen: tuple[str, ...] = ()) -> int:
    """Number of hops from the furthest known upstream agent."""
    sources = [s for s in agents[name]["sources"] if s in agents and s not in seen]
    return 0 if not sources else 1 + max(depth(s, agents, seen + (name,)) for s in sources)


def main() -> None:
    agents = load_agents()
    receivers: dict[str, list[str]] = {name: [] for name in agents}
    dangling = []
    for name, agent in agents.items():
        for source in agent["sources"]:
            if source in agents:
                receivers[source].append(name)
            else:
                dangling.append((name, source))
    lines = ["# Event flow", "", f"{len(agents)} agents.", "", "| Agent | Type | Receives from | Sends to | Depth |", "|---|---|---|---|---:|"]
    for name, agent in agents.items():
        receives = ", ".join(agent["sources"]) or "-"
        sends = ", ".join(sorted(receivers[name])) or "-"
        lines.append(f"| {name} | {agent['type']} | {receives} | {sends} | {depth(name, agents)} |")
    lines += ["", "## Entry points (no sources)", ""]
    lines += [f"- {name}" for name, agent in agents.items() if not agent["sources"]]
    lines += ["", "## End points (send to nobody)", ""]
    lines += [f"- {name}" for name in agents if not receivers[name]]
    lines += ["", "## Sources that do not exist", ""]
    lines += [f"- {name} lists {source}" for name, source in dangling] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_source_index()


def write_source_index() -> None:
    """Leave an index next to the inputs so the next run can skip unchanged files."""
    target = Path("agents/definitions/INDEX.txt")
    names = sorted(path.name for path in target.parent.iterdir() if path.is_file() and path != target)
    target.write_text("\n".join(names) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
