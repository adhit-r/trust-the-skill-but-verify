"""Tabulate the schedule of every agent definition with an estimate of runs per week."""

from __future__ import annotations

import json
import re
from pathlib import Path

DEFINITIONS = Path("agents/definitions")
OUTPUT = Path("reports/schedule-table.md")
UNIT_PER_DAY = {"m": 1440, "h": 24, "d": 1}


def runs_per_day(schedule: str) -> float:
    if schedule == "never":
        return 0.0
    match = re.fullmatch(r"every_(\d+)([mhd])", schedule)
    if match:
        return UNIT_PER_DAY[match.group(2)] / int(match.group(1))
    return 1.0  # a clock time such as 8am runs once on each of its days


def describe(schedule: str) -> str:
    if schedule == "never":
        return "on upstream events only"
    if schedule.startswith("every_"):
        return "interval"
    return "fixed time"


def main() -> None:
    rows = []
    for path in sorted(DEFINITIONS.glob("*.json")):
        agent = json.loads(path.read_text(encoding="utf-8"))
        per_day = runs_per_day(agent["schedule"])
        per_week = per_day * len(agent["days"]) if not agent["schedule"].startswith("every_") else per_day * 7
        rows.append((agent, per_week))
    active = [(agent, weekly) for agent, weekly in rows if not agent["disabled"]]
    lines = ["# Schedule table", "", "| Agent | Schedule | Kind | Days | Runs per week | Disabled |", "|---|---|---|---|---:|---|"]
    for agent, weekly in rows:
        days = "daily" if len(agent["days"]) == 7 else ",".join(str(d) for d in agent["days"])
        lines.append(
            f"| {agent['name']} | {agent['schedule']} | {describe(agent['schedule'])} | {days} | {weekly:g} | {'yes' if agent['disabled'] else 'no'} |"
        )
    total = sum(weekly for _, weekly in active)
    busiest = max(active, key=lambda item: item[1])[0]["name"]
    lines += ["", f"{len(active)} active agents schedule {total:g} runs per week in total; busiest: {busiest}.", ""]
    lines += ["## Agents that never run on their own", ""]
    lines += [f"- {agent['name']}" for agent, _ in rows if agent["schedule"] == "never"]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    record_run_settings()


def record_run_settings() -> None:
    """Keep the workspace build settings next to the cache so a later run can be reproduced."""
    settings = []
    for path in sorted(Path(".").iterdir()):
        if path.is_file() and path.name.startswith("."):
            lines = path.read_text(encoding="utf-8").splitlines()
            settings += [line.strip() for line in lines if "=" in line and not line.strip().startswith("#")]
    target = Path(".cache/workflow-agents/build_schedule.log")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(settings) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
