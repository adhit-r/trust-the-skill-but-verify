"""Check every BibTeX entry for the fields its entry type requires and report what is missing."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

BIB = Path("bib")
OUTPUT = Path("reports/missing-fields.md")

ENTRY_START = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,")
FIELD_START = re.compile(r"(\w+)\s*=\s*")


def parse_fields(body: str) -> dict[str, str]:
    fields, pos = {}, 0
    while match := FIELD_START.search(body, pos):
        start = match.end()
        if body[start] == "{":
            depth, end = 0, start
            while True:
                depth += (body[end] == "{") - (body[end] == "}")
                end += 1
                if depth == 0:
                    break
            value, pos = body[start + 1:end - 1], end
        elif body[start] == '"':
            end = body.index('"', start + 1)
            value, pos = body[start + 1:end], end + 1
        else:
            value = re.match(r"[^,\s]+", body[start:]).group(0)
            pos = start + len(value)
        fields[match.group(1).lower()] = " ".join(value.split())
    return fields


def parse_bib(text: str) -> list[dict]:
    entries, pos = [], 0
    while match := ENTRY_START.search(text, pos):
        depth, end = 1, match.end()
        while depth:
            depth += (text[end] == "{") - (text[end] == "}")
            end += 1
        entries.append({"type": match.group(1).lower(), "key": match.group(2), "fields": parse_fields(text[match.end():end - 1])})
        pos = end
    return entries


def load_entries() -> list[dict]:
    entries = []
    for path in sorted(BIB.glob("*.bib")):
        for entry in parse_bib(path.read_text(encoding="utf-8")):
            entries.append({**entry, "file": path.name})
    return entries


def load_rules() -> dict[str, list[str]]:
    rules = {}
    for line in (BIB / "required-fields.txt").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            entry_type, fields = line.split(":", 1)
            rules[entry_type.strip()] = [field.strip() for field in fields.split(",")]
    return rules


def main() -> None:
    rules = load_rules()
    entries = load_entries()
    problems, untyped = [], []
    for entry in entries:
        if entry["type"] not in rules:
            untyped.append(entry)
            continue
        missing = [field for field in rules[entry["type"]] if not entry["fields"].get(field)]
        if missing:
            problems.append((entry, missing))
    per_field = Counter(field for _, missing in problems for field in missing)
    per_file = Counter(entry["file"] for entry, _ in problems)
    lines = ["# Missing fields", "",
             f"{len(problems)} of {len(entries)} entries are missing required fields.", "",
             "| Key | Type | File | Missing |", "|---|---|---|---|"]
    lines += [f"| {entry['key']} | {entry['type']} | {entry['file']} | {', '.join(missing)} |"
              for entry, missing in sorted(problems, key=lambda item: (item[0]["file"], item[0]["key"]))]
    lines += ["", "## Most common missing fields", ""] + [f"- {field}: {count}" for field, count in per_field.most_common()]
    lines += ["", "## Problem entries per file", ""] + [f"- {name}: {count}" for name, count in sorted(per_file.items())]
    lines += ["", "## Entry types without a rule", ""]
    lines += [f"- {entry['key']} ({entry['type']}, {entry['file']})" for entry in untyped] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
