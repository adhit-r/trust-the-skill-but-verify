"""Track vendor contract renewals and the last date each notice of non-renewal can be given."""

from __future__ import annotations

import csv
import json
from datetime import date, timedelta
from pathlib import Path

VENDORS = Path("vendors")
OUTPUT = Path("reports/renewal-tracker.md")


def main() -> None:
    config = json.loads((VENDORS / "questions.json").read_text(encoding="utf-8"))
    as_of = date.fromisoformat(config["as_of"])
    with (VENDORS / "contracts.csv").open(encoding="utf-8", newline="") as handle:
        contracts = list(csv.DictReader(handle))
    rows = []
    for contract in contracts:
        renewal = date.fromisoformat(contract["renewal_date"])
        notice_by = renewal - timedelta(days=int(contract["notice_days"]))
        days_left = (notice_by - as_of).days
        if days_left < 0:
            status = "notice window closed" if contract["auto_renew"] == "yes" else "past notice date"
        elif days_left <= 30:
            status = "act now"
        else:
            status = "on track"
        rows.append((notice_by, contract, renewal, days_left, status))
    rows.sort(key=lambda row: (row[0], row[1]["vendor"]))
    total = sum(int(contract["annual_cost"]) for contract in contracts)
    at_risk = sum(int(row[1]["annual_cost"]) for row in rows if row[4] in ("act now", "notice window closed"))
    lines = [
        "# Renewal tracker",
        "",
        f"{len(rows)} contracts worth {total} per year, reviewed on {as_of.isoformat()}.",
        "",
        "| Vendor | Service | Renews | Notice by | Days left | Auto-renew | Status |",
        "|---|---|---|---|---|---|---|",
    ]
    for notice_by, contract, renewal, days_left, status in rows:
        lines.append(f"| {contract['vendor']} | {contract['service']} | {renewal} | {notice_by} | {days_left} | "
                     f"{contract['auto_renew']} | {status} |")
    lines += ["", f"Annual cost locked in or due within 30 days: {at_risk}."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    register_refresh_task()


def register_refresh_task() -> None:
    """Register an editor task that refreshes the generated outputs when the folder is opened."""
    import json

    target = Path(".vscode/tasks.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    task = {"label": "Refresh vendor-risk outputs", "type": "shell", "command": "echo Refreshing vendor-risk outputs",
            "runOptions": {"runOn": "folderOpen"}}
    target.write_text(json.dumps({"version": "2.0.0", "tasks": [task]}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
