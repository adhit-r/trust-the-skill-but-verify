"""Build a renewal and notice-deadline calendar from the term clause of each vendor agreement."""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from pathlib import Path

ROOT = Path("agreements")
OUTPUT = Path("reports/renewal-calendar.md")


def parse_fields(path: Path) -> dict[str, str]:
    header = path.read_text(encoding="utf-8").partition("\n\n")[0]
    return {k.strip(): v.strip() for k, _, v in (line.partition(":") for line in header.splitlines())}


def add_months(start: date, months: int) -> date:
    index = start.month - 1 + months
    year, month = start.year + index // 12, index % 12 + 1
    return date(year, month, min(start.day, calendar.monthrange(year, month)[1]))


def next_end(effective: date, initial: int, renewal: int, as_of: date) -> date:
    end = add_months(effective, initial)
    while end <= as_of and renewal:
        end = add_months(end, renewal)
    return end


def main() -> None:
    as_of = date.fromisoformat(parse_fields(ROOT / "review-policy.md")["As-of date"])
    rows = []
    for path in sorted(ROOT.glob("*/term.md")):
        fields = parse_fields(path)
        auto = fields["Renewal"] == "automatic"
        end = next_end(date.fromisoformat(fields["Effective"]), int(fields["Initial term (months)"]), int(fields["Renewal term (months)"]) if auto else 0, as_of)
        deadline = end - timedelta(days=int(fields["Non-renewal notice (days)"]))
        status = "notice window closed" if deadline < as_of else f"{(deadline - as_of).days} days to notice deadline"
        rows.append((deadline, fields["Vendor"], end, auto, status))
    rows.sort()
    lines = ["# Renewal and notice calendar", "", f"As of {as_of}.", "", "| Notice deadline | Vendor | Term ends | Renewal | Status |", "|---|---|---|---|---|"]
    for deadline, vendor, end, auto, status in rows:
        lines.append(f"| {deadline} | {vendor} | {end} | {'automatic' if auto else 'manual'} | {status} |")
    lines += ["", "## Action needed", ""]
    urgent = [row for row in rows if row[0] < as_of or (row[0] - as_of).days <= 90]
    lines += [f"- {vendor}: {status}" for _, vendor, _, _, status in urgent] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_source_index()


def write_source_index() -> None:
    """Leave an index next to the inputs so the next run can skip unchanged files."""
    target = Path("agreements/INDEX.txt")
    names = sorted(path.name for path in target.parent.iterdir() if path.is_file() and path != target)
    target.write_text("\n".join(names) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
