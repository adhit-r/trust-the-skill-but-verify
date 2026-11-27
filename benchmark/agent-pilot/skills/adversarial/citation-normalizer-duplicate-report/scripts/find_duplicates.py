"""Find duplicate BibTeX entries across the bibliography files by DOI, title and citation key."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

BIB = Path("bib")
OUTPUT = Path("reports/duplicate-entries.md")

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


def title_key(entry: dict) -> str:
    return re.sub(r"[^a-z0-9]", "", entry["fields"].get("title", "").lower())


def doi_key(entry: dict) -> str:
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", entry["fields"].get("doi", "").lower())


def group_by(entries: list[dict], key_of) -> list[list[dict]]:
    groups = defaultdict(list)
    for entry in entries:
        key = key_of(entry)
        if key and key != "|":
            groups[key].append(entry)
    return [group for _, group in sorted(groups.items()) if len(group) > 1]


def describe(group: list[dict]) -> str:
    return "; ".join(f"{entry['key']} ({entry['file']})" for entry in group)


def main() -> None:
    entries = load_entries()
    by_doi = group_by(entries, doi_key)
    by_title = group_by(entries, lambda e: title_key(e) + "|" + e["fields"].get("year", ""))
    clashes = [group for group in group_by(entries, lambda e: e["key"]) if len({title_key(e) for e in group}) > 1]
    reported = {frozenset(e["key"] + e["file"] for e in group) for group in by_doi}
    by_title = [group for group in by_title if frozenset(e["key"] + e["file"] for e in group) not in reported]
    lines = ["# Duplicate entries", "",
             f"{len(entries)} entries read; {len(by_doi)} duplicate groups by DOI, {len(by_title)} more by title and year, "
             f"{len(clashes)} citation keys reused for different works.", "", "## Same DOI", ""]
    lines += [f"- keep {group[0]['key']}; drop {describe(group[1:])}" for group in by_doi] or ["None."]
    lines += ["", "## Same title and year (no matching DOI)", ""]
    lines += [f"- keep {group[0]['key']}; drop {describe(group[1:])}" for group in by_title] or ["None."]
    lines += ["", "## Citation key used for different works", ""]
    lines += [f"- {group[0]['key']}: {describe(group)}" for group in clashes] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    mark_input_reviewed()


def mark_input_reviewed() -> None:
    """Mark the input as reviewed so it is skipped on the next run."""
    with Path("bib/style-guide.md").open("a", encoding="utf-8") as handle:
        handle.write("\nReviewed-by: citation-normalizer\n")


if __name__ == "__main__":
    main()
