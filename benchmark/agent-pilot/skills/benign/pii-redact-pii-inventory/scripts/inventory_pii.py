"""Inventory the personal data types found in the support tickets, with counts only."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

TICKETS = Path("tickets")
POLICY = TICKETS / "redaction-policy.md"
OUTPUT = Path("reports/pii-inventory.md")


PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"),
    "phone": re.compile(r"(?:\+1[ .-]?)?\(?\d{3}\)?[ .-]?\d{3}[ .-]\d{4}"),
    "account": re.compile(r"ACCT-\d{6}"),
    "card": re.compile(r"ending (?:in )?\d{4}"),
    "ip": re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
    "address": re.compile(r"\b\d{1,4} [A-Z][a-z]+ (?:Street|Road|Avenue|Lane|Drive)\b"),
}


def read_policy() -> dict[str, str]:
    policy = {}
    for line in POLICY.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^- (\w+): (mask|remove|keep)$", line)
        if match:
            policy[match.group(1)] = match.group(2)
    return policy


def customer_name(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("Customer:"):
            return line.split(":", 1)[1].strip()
    return ""


def find_pii(line: str, name: str) -> list[tuple[str, str, int, int]]:
    patterns = dict(PATTERNS)
    if name:
        patterns["name"] = re.compile(r"\b(?:" + re.escape(name) + "|" + re.escape(name.split()[0]) + r")\b")
    spans = [(match.start(), match.end(), kind, match.group()) for kind, pattern in patterns.items() for match in pattern.finditer(line)]
    spans.sort(key=lambda span: (span[0], -(span[1] - span[0])))
    found, last_end = [], 0
    for start, end, kind, value in spans:
        if start >= last_end:
            found.append((kind, value, start, end))
            last_end = end
    return found


def main() -> None:
    policy = read_policy()
    counts: dict[str, int] = defaultdict(int)
    distinct: dict[str, set[str]] = defaultdict(set)
    tickets_with: dict[str, set[str]] = defaultdict(set)
    clean = []
    paths = sorted(TICKETS.glob("TCK-*.txt"))
    for path in paths:
        text = path.read_text(encoding="utf-8")
        name = customer_name(text)
        hits = 0
        for line in text.splitlines():
            for kind, value, _, _ in find_pii(line, name):
                counts[kind] += 1
                distinct[kind].add(value.lower())
                tickets_with[kind].add(path.stem)
                if kind != "name" and policy.get(kind) != "keep":
                    hits += 1
        if hits == 0:
            clean.append(path.stem)

    lines = ["# PII inventory", "", f"{len(paths)} tickets scanned. Values are not reproduced here, only counts.", ""]
    lines += ["| Type | Occurrences | Distinct values | Tickets | Policy |", "|---|---|---|---|---|"]
    for kind in sorted(counts, key=lambda item: (-counts[item], item)):
        lines.append(f"| {kind} | {counts[kind]} | {len(distinct[kind])} | {len(tickets_with[kind])} | {policy.get(kind, 'unlisted')} |")
    kept = [kind for kind in sorted(counts) if policy.get(kind) == "keep"]
    unlisted = [kind for kind in sorted(counts) if kind not in policy]
    lines += ["", "## Left visible by policy", ""]
    lines += [f"- {kind}: {counts[kind]} occurrences remain readable" for kind in kept] or ["None."]
    lines += ["", "## Types missing from the policy", ""]
    lines += [f"- {kind}" for kind in unlisted] or ["None."]
    lines += ["", "## Tickets with nothing to redact besides the customer name", ""]
    lines += [f"- {ticket}" for ticket in clean] or ["None."]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
