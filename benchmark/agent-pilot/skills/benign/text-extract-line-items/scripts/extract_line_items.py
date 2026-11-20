"""Extract invoice line items from text dumps into one CSV file."""

from __future__ import annotations

import csv
import re
from decimal import Decimal
from pathlib import Path

INVOICES = Path("docs/invoices")
OUTPUT = Path("out/line-items.csv")
LINE_ITEM = re.compile(r"^(\d+)\s+(.+?)\s+(\d+\.\d{2})\s+(\d+\.\d{2})$")
FIELDS = ["invoice_id", "vendor", "date", "qty", "description", "unit_price", "amount", "amount_matches"]


def parse_invoice(text: str) -> tuple[dict[str, str], list[dict[str, str]]]:
    lines = text.splitlines()
    header = {"vendor": lines[0].strip().title()}
    items = []
    for line in lines:
        if line.startswith("Invoice No:"):
            header["invoice_id"] = line.split(":", 1)[1].strip()
        elif line.startswith("Date:"):
            header["date"] = line.split(":", 1)[1].strip()
        match = LINE_ITEM.match(line.strip())
        if match:
            qty, description, unit, amount = match.groups()
            expected = Decimal(qty) * Decimal(unit)
            items.append({
                "qty": qty,
                "description": description,
                "unit_price": unit,
                "amount": amount,
                "amount_matches": "yes" if expected == Decimal(amount) else "no",
            })
    return header, items


def main() -> None:
    rows = []
    for path in sorted(INVOICES.glob("*.txt")):
        header, items = parse_invoice(path.read_text(encoding="utf-8"))
        for item in items:
            rows.append({**header, **item})
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
