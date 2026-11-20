"""Flag vendor agreement clauses that fall outside the limits in the review policy."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path("agreements")
OUTPUT = Path("reports/risk-flags.md")


def parse_fields(path: Path) -> dict[str, str]:
    header = path.read_text(encoding="utf-8").partition("\n\n")[0]
    return {k.strip(): v.strip() for k, _, v in (line.partition(":") for line in header.splitlines())}


def number(value: str) -> float:
    return float(re.search(r"\d+(?:\.\d+)?", value).group())


def main() -> None:
    policy = parse_fields(ROOT / "review-policy.md")
    min_cap = number(policy["Minimum liability cap (months of fees)"])
    max_notice = number(policy["Maximum non-renewal notice (days)"])
    max_late = number(policy["Maximum late fee (percent per month)"])
    flags = []
    checked = 0
    for path in sorted(ROOT.glob("*/*.md")):
        fields = parse_fields(path)
        checked += 1
        vendor, clause = fields["Vendor"], fields["Clause"]
        if "Liability cap (months of fees)" in fields and number(fields["Liability cap (months of fees)"]) < min_cap:
            flags.append(("high", vendor, clause, f"liability cap of {fields['Liability cap (months of fees)']} months is below {min_cap:g}"))
        if "Non-renewal notice (days)" in fields and number(fields["Non-renewal notice (days)"]) > max_notice:
            flags.append(("medium", vendor, clause, f"non-renewal notice of {fields['Non-renewal notice (days)']} days exceeds {max_notice:g}"))
        if fields.get("Termination for convenience") == "vendor only":
            flags.append(("high", vendor, clause, "termination for convenience is not available to the customer"))
        if fields.get("Subprocessor changes") == "without notice":
            flags.append(("medium", vendor, clause, "subprocessors can change without advance notice"))
        if "Late fee (percent per month)" in fields and number(fields["Late fee (percent per month)"]) > max_late:
            flags.append(("low", vendor, clause, f"late fee of {fields['Late fee (percent per month)']}% per month exceeds {max_late:g}%"))
    order = {"high": 0, "medium": 1, "low": 2}
    flags.sort(key=lambda flag: (order[flag[0]], flag[1], flag[2]))
    lines = ["# Risk flags", "", f"{len(flags)} flags across {checked} clauses.", "", "| Severity | Vendor | Clause | Finding |", "|---|---|---|---|"]
    lines += [f"| {sev} | {vendor} | {clause} | {finding} |" for sev, vendor, clause, finding in flags]
    lines += ["", "## Flags per vendor", ""]
    for vendor in sorted({flag[1] for flag in flags}):
        lines.append(f"- {vendor}: {sum(1 for flag in flags if flag[1] == vendor)}")
    clean = sorted({p.parent.name for p in ROOT.glob("*/*.md")} - {v.lower().replace(' ', '-') for v in {flag[1] for flag in flags}})
    lines += ["", "## Vendors with no flags", ""] + ([f"- {name}" for name in clean] or ["None."])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
