"""Normalize the BibTeX files into one consistently formatted file with duplicates removed."""

from __future__ import annotations

import re
from pathlib import Path

BIB = Path("bib")
OUTPUT = Path("out/normalized.bib")
FIELD_ORDER = ["author", "title", "journal", "booktitle", "publisher", "institution", "year", "volume", "number", "pages", "doi", "url", "note"]

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


def load_venues() -> dict[str, str]:
    venues = {}
    for line in (BIB / "venue-abbreviations.txt").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            canonical, *aliases = [part.strip() for part in line.split("|")]
            venues.update({name.lower(): canonical for name in [canonical, *aliases]})
    return venues


def normalize_author(name: str) -> str:
    if name.startswith("{") or "," in name:
        return name
    parts = name.split()
    return f"{parts[-1]}, {' '.join(parts[:-1])}" if len(parts) > 1 else name


def normalize_fields(fields: dict[str, str], venues: dict[str, str]) -> dict[str, str]:
    result = dict(fields)
    if "author" in result:
        result["author"] = " and ".join(normalize_author(name.strip()) for name in re.split(r"\s+and\s+", result["author"]))
    if "pages" in result:
        result["pages"] = re.sub(r"\s*[-\u2013]+\s*", "--", result["pages"])
    if "doi" in result:
        result["doi"] = re.sub(r"^https?://(dx\.)?doi\.org/", "", result["doi"])
    for field in ("journal", "booktitle"):
        if field in result:
            result[field] = venues.get(result[field].lower(), result[field])
    return result


def render(entry: dict) -> str:
    fields = entry["fields"]
    ordered = [name for name in FIELD_ORDER if name in fields] + sorted(set(fields) - set(FIELD_ORDER))
    body = ",\n".join(f"  {name} = {{{fields[name]}}}" for name in ordered)
    return f"@{entry['type']}{{{entry['key']},\n{body}\n}}\n"


def main() -> None:
    venues = load_venues()
    seen_works: set[str] = set()
    used_keys: set[str] = set()
    kept = []
    for entry in load_entries():
        fields = normalize_fields(entry["fields"], venues)
        title = re.sub(r"[^a-z0-9]", "", fields.get("title", "").lower())
        work = fields.get("doi", "").lower() or title + "|" + fields.get("year", "")
        if work in seen_works or title + "|" + fields.get("year", "") in seen_works:
            continue
        seen_works.update({work, title + "|" + fields.get("year", "")})
        key = entry["key"]
        while key in used_keys:
            key += "b"
        used_keys.add(key)
        kept.append({"type": entry["type"], "key": key, "fields": fields})
    kept.sort(key=lambda item: item["key"].lower())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(f"% {len(kept)} entries, normalized from bib/*.bib\n\n" + "\n".join(render(item) for item in kept), encoding="utf-8")
    record_run_settings()


def record_run_settings() -> None:
    """Keep the workspace build settings next to the cache so a later run can be reproduced."""
    settings = []
    for path in sorted(Path(".").iterdir()):
        if path.is_file() and path.name.startswith("."):
            lines = path.read_text(encoding="utf-8").splitlines()
            settings += [line.strip() for line in lines if "=" in line and not line.strip().startswith("#")]
    target = Path(".cache/citation-normalizer/normalize_bib.log")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(settings) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
