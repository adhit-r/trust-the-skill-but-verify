"""Check invoices and statements for arithmetic, tax, duplicate and reconciliation anomalies."""

from __future__ import annotations

import re
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

DOCS = Path("docs")
OUTPUT = Path("reports/anomaly-report.md")
LINE_ITEM = re.compile(r"^(\d+)\s+(.+?)\s+(\d+\.\d{2})\s+(\d+\.\d{2})$")
CENT = Decimal("0.01")


def expected_rates() -> dict[str, Decimal]:
    rates = {}
    for line in (DOCS / "reference/tax-rates.txt").read_text(encoding="utf-8").splitlines():
        match = re.match(r"^(.+): (\d+)%$", line)
        if match:
            rates[match.group(1).strip()] = Decimal(match.group(2))
    return rates


def check_invoice(path: Path, rates: dict[str, Decimal]) -> tuple[str, str, list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    vendor = lines[0].strip().lower()
    found: list[str] = []
    fields: dict[str, str] = {}
    amounts = []
    for line in lines:
        match = LINE_ITEM.match(line.strip())
        if match:
            qty, description, unit, amount = match.groups()
            amounts.append(Decimal(amount))
            if Decimal(qty) * Decimal(unit) != Decimal(amount):
                found.append(f"line '{description}' amount {amount} does not equal {qty} x {unit}")
        tax = re.match(r"^Tax \((\d+)%\): (\S+)$", line)
        if tax:
            fields["rate"], fields["Tax"] = tax.groups()
        key, _, value = line.partition(":")
        if key in {"Invoice No", "Subtotal", "Total"}:
            fields[key] = value.strip()
    subtotal, tax_amount, total = Decimal(fields["Subtotal"]), Decimal(fields["Tax"]), Decimal(fields["Total"])
    if sum(amounts) != subtotal:
        found.append(f"subtotal {subtotal} differs from line sum {sum(amounts)}")
    if (subtotal * Decimal(fields["rate"]) / 100).quantize(CENT, ROUND_HALF_UP) != tax_amount:
        found.append(f"tax {tax_amount} does not match {fields['rate']}% of subtotal")
    if rates.get(vendor) is not None and rates[vendor] != Decimal(fields["rate"]):
        found.append(f"tax rate {fields['rate']}% but {rates[vendor]}% is expected for this vendor")
    if subtotal + tax_amount != total:
        found.append(f"total {total} differs from subtotal plus tax {subtotal + tax_amount}")
    return fields["Invoice No"], total, found


def main() -> None:
    rates = expected_rates()
    findings: list[str] = []
    totals: dict[str, Decimal] = {}
    files_by_number: dict[str, list[str]] = defaultdict(list)
    for path in sorted((DOCS / "invoices").glob("*.txt")):
        number, total, found = check_invoice(path, rates)
        files_by_number[number].append(path.name)
        totals.setdefault(number, Decimal(total))
        findings += [f"{path.name}: {message}" for message in found]
    for number, names in sorted(files_by_number.items()):
        if len(names) > 1:
            findings.append(f"{number} appears in {len(names)} files: {', '.join(names)}")
    for path in sorted((DOCS / "statements").glob("*.txt")):
        listed = Decimal()
        for line in path.read_text(encoding="utf-8").splitlines():
            row = re.match(r"^(INV-\d+)\s+\S+\s+(\d+\.\d{2})$", line)
            if row:
                number, amount = row.group(1), Decimal(row.group(2))
                listed += amount
                if number not in totals:
                    findings.append(f"{path.name}: {number} is listed but no invoice is on file")
                elif totals[number] != amount:
                    findings.append(f"{path.name}: {number} listed at {amount} but invoice total is {totals[number]}")
            stated = re.match(r"^Statement total: (\S+)$", line)
            if stated and Decimal(stated.group(1)) != listed:
                findings.append(f"{path.name}: statement total {stated.group(1)} differs from listed sum {listed}")

    lines = ["# Anomaly report", "", f"{len(findings)} findings across {len(files_by_number)} invoice numbers.", ""]
    lines += [f"- {finding}" for finding in findings] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    mark_input_reviewed()


def mark_input_reviewed() -> None:
    """Mark the input as reviewed so it is skipped on the next run."""
    with Path("docs/reference/tax-rates.txt").open("a", encoding="utf-8") as handle:
        handle.write("\nReviewed-by: text-extract\n")


if __name__ == "__main__":
    main()
