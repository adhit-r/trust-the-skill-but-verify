"""Write a per-ticket log of where redactions apply, with line numbers and no values."""

from __future__ import annotations

import re
import csv
from collections import Counter
from pathlib import Path

TICKETS = Path("tickets")
POLICY = TICKETS / "redaction-policy.md"
INDEX = TICKETS / "index.csv"
OUTPUT = Path("reports/redaction-log.md")


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


def read_queues() -> dict[str, str]:
    with INDEX.open(encoding="utf-8", newline="") as handle:
        return {row["ticket"]: row["queue"] for row in csv.DictReader(handle)}


def main() -> None:
    policy = read_policy()
    queues = read_queues()
    lines = ["# Redaction log", ""]
    by_queue: Counter[str] = Counter()
    total = 0
    for path in sorted(TICKETS.glob("TCK-*.txt")):
        text = path.read_text(encoding="utf-8")
        name = customer_name(text)
        entries = []
        for number, line in enumerate(text.splitlines(), 1):
            for kind, _, _, _ in find_pii(line, name):
                action = policy.get(kind, "mask")
                if action != "keep":
                    entries.append(f"- line {number}: {kind} {'removed' if action == 'remove' else 'masked'}")
        queue = queues.get(path.stem, "unknown")
        by_queue[queue] += len(entries)
        total += len(entries)
        lines += [f"## {path.stem} ({queue})", ""] + (entries or ["- nothing to redact"]) + [""]
    lines += ["## Totals", "", f"{total} redactions across {len(queues)} tickets.", ""]
    lines += [f"- {queue}: {count}" for queue, count in sorted(by_queue.items())]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
