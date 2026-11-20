"""Summarise invoice totals per vendor and per month from the invoice text dumps."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from pathlib import Path

INVOICES = Path("docs/invoices")
OUTPUT = Path("reports/totals-summary.md")


def read_fields(text: str) -> dict[str, str]:
    fields = {"vendor": text.splitlines()[0].strip().title()}
    for line in text.splitlines():
        key, sep, value = line.partition(":")
        if not sep:
            continue
        if key.startswith("Tax ("):
            key = "Tax"
        if key in {"Invoice No", "Date", "Subtotal", "Tax", "Total"}:
            fields[key] = value.strip()
    return fields


def money(value: Decimal) -> str:
    return f"{value:,.2f}"


def main() -> None:
    invoices = [read_fields(path.read_text(encoding="utf-8")) for path in sorted(INVOICES.glob("*.txt"))]
    vendors: dict[str, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    months: dict[str, Decimal] = defaultdict(Decimal)
    for invoice in invoices:
        totals = vendors[invoice["vendor"]]
        totals["count"] += 1
        totals["subtotal"] += Decimal(invoice["Subtotal"])
        totals["tax"] += Decimal(invoice["Tax"])
        totals["total"] += Decimal(invoice["Total"])
        months[invoice["Date"][:7]] += Decimal(invoice["Total"])

    grand = sum((totals["total"] for totals in vendors.values()), Decimal())
    tax = sum((totals["tax"] for totals in vendors.values()), Decimal())
    lines = [
        "# Invoice totals summary",
        "",
        f"{len(invoices)} invoices from {len(vendors)} vendors. Grand total {money(grand)}, of which tax {money(tax)}.",
        "",
        "| Vendor | Invoices | Subtotal | Tax | Total | Share |",
        "|---|---|---|---|---|---|",
    ]
    for vendor, totals in sorted(vendors.items(), key=lambda item: (-item[1]["total"], item[0])):
        share = totals["total"] / grand * 100
        lines.append(f"| {vendor} | {int(totals['count'])} | {money(totals['subtotal'])} | {money(totals['tax'])} | {money(totals['total'])} | {share:.1f}% |")
    lines += ["", "## By month", ""]
    lines += [f"- {month}: {money(total)}" for month, total in sorted(months.items())]
    largest = max(invoices, key=lambda invoice: Decimal(invoice["Total"]))
    lines += ["", f"Largest invoice: {largest['Invoice No']} from {largest['vendor']} at {money(Decimal(largest['Total']))}."]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
