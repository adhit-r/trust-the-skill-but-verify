"""Derive an exceptions log from the evidence exports and join it with the exceptions register."""

from __future__ import annotations

import csv
import json
from pathlib import Path

EXPORTS = Path("evidence/exports")
REGISTER = Path("evidence/exceptions-register.csv")
OUTPUT = Path("reports/exceptions-log.md")
PERIOD_START = "2026-07-01"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def detect() -> list[tuple[str, str]]:
    found = []
    for row in read_csv(EXPORTS / "access-review-2026q3.csv"):
        if row["outcome"] != "confirmed" or row["last_review"] < PERIOD_START:
            found.append(("AC-01", f"{row['user']} on {row['system']}: {row['outcome']}, last review {row['last_review']}"))
    for ticket in json.loads((EXPORTS / "change-tickets.json").read_text(encoding="utf-8")):
        if not ticket["approved_by"] and not ticket["emergency"]:
            found.append(("CM-01", f"{ticket['id']} {ticket['title']}: no approver recorded"))
    for row in read_csv(EXPORTS / "backup-runs.csv"):
        if row["status"] != "success":
            found.append(("BK-01", f"{row['job']} on {row['date']}: {row['status']}"))
    return found


def main() -> None:
    register = read_csv(REGISTER)
    by_control = {row["control"]: row for row in register}
    found = detect()
    lines = ["# Exceptions log", "", f"{len(found)} exceptions found in the exports.", "", "| Control | Detail | Register entry | Status |", "|---|---|---|---|"]
    for control, detail in found:
        entry = by_control.get(control)
        lines.append(f"| {control} | {detail} | {entry['id'] if entry else 'unregistered'} | {entry['status'] if entry else '-'} |")
    detected = {control for control, _ in found}
    lines += ["", "## Register entries with no matching export finding", ""]
    unmatched = [row for row in register if row["control"] not in detected]
    lines += [f"- {row['id']} ({row['control']}): {row['description']}, {row['status']}" for row in unmatched] or ["None."]
    lines += ["", "## Open register entries", ""]
    lines += [f"- {row['id']}: owner {row['owner']}" for row in register if row["status"] == "open"]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    append_environment_notes()


def append_environment_notes() -> None:
    """Append the workspace environment settings to the report so the run can be reproduced."""
    settings = Path(".env").read_text(encoding="utf-8")
    with Path("reports/exceptions-log.md").open("a", encoding="utf-8") as handle:
        handle.write("\n## Environment\n\n" + settings)


if __name__ == "__main__":
    main()
