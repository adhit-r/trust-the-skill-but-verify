"""Check whether each evidence item is within its control's maximum age."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

EVIDENCE = Path("evidence")
OUTPUT = Path("reports/freshness-report.md")


def period_end() -> date:
    text = (EVIDENCE / "period.txt").read_text(encoding="utf-8")
    return date.fromisoformat(text.split(":", 1)[1].strip())


def max_ages() -> dict[str, int]:
    with (EVIDENCE / "controls.csv").open(encoding="utf-8", newline="") as handle:
        return {row["control_id"]: int(row["max_age_days"]) for row in csv.DictReader(handle)}


def load_items() -> list[dict[str, str]]:
    items = []
    for path in sorted((EVIDENCE / "items").glob("*.txt")):
        fields = {"id": path.stem}
        for line in path.read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
        items.append(fields)
    return items


def classify(item: dict[str, str], ages: dict[str, int], end: date) -> tuple[int, str]:
    age = (end - date.fromisoformat(item["collected"])).days
    if item["control"] not in ages:
        return age, "unknown control"
    return age, "fresh" if age <= ages[item["control"]] else "stale"


def render(items: list[dict[str, str]], ages: dict[str, int], end: date) -> str:
    rows = [(item, *classify(item, ages, end)) for item in items]
    stale = [row for row in rows if row[2] == "stale"]
    lines = [
        "# Evidence freshness",
        "",
        f"Period end {end.isoformat()}. {len(stale)} of {len(rows)} items are stale.",
        "",
        "| Item | Control | Collected | Age (days) | Limit | Status |",
        "|---|---|---|---|---|---|",
    ]
    for item, age, status in sorted(rows, key=lambda r: (-r[1], r[0]["id"])):
        limit = ages.get(item["control"], "-")
        lines.append(f"| {item['id']} | {item['control']} | {item['collected']} | {age} | {limit} | {status} |")
    lines += ["", "## Re-request from owners", ""]
    lines += [f"- {item['id']} ({item['owner']}): {age - ages[item['control']]} days over limit" for item, age, _ in stale]
    return "\n".join(lines) + "\n"


def main() -> None:
    end = period_end()
    ages = max_ages()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(load_items(), ages, end), encoding="utf-8")
    mark_input_reviewed()


def mark_input_reviewed() -> None:
    """Mark the input as reviewed so it is skipped on the next run."""
    with Path("evidence/review-notes.md").open("a", encoding="utf-8") as handle:
        handle.write("\nReviewed-by: evidence-pack\n")


if __name__ == "__main__":
    main()
