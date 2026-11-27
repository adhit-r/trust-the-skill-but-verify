"""Assemble the book chapters listed in SUMMARY.md into a single Markdown page."""

from __future__ import annotations

import re
from pathlib import Path

SOURCE = Path("book/src")
OUTPUT = Path("out/book.md")
ENTRY = re.compile(r"^(\s*)(?:[-*]\s+)?\[(.+?)\]\((.+?)\)\s*$")


def summary_entries() -> list[tuple[int, str, str]]:
    entries = []
    for line in (SOURCE / "SUMMARY.md").read_text(encoding="utf-8").splitlines():
        match = ENTRY.match(line)
        if match:
            depth = len(match.group(1)) // 2
            entries.append((depth, match.group(2), match.group(3)))
    return entries


def shift_headings(text: str, extra: int) -> str:
    """Push every heading down by `extra` levels, ignoring fenced code."""
    out, fenced = [], False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"#{1,5} ", line):
            line = "#" * extra + line
        out.append(line)
    return "\n".join(out)


def main() -> None:
    parts, missing, words = [], [], 0
    for depth, title, target in summary_entries():
        path = SOURCE / target
        if not path.is_file():
            missing.append(target)
            continue
        body = path.read_text(encoding="utf-8")
        words += len(body.split())
        parts.append(f"<!-- {target} -->\n" + shift_headings(body, depth))
    header = [
        "# The assembled book",
        "",
        f"{len(parts)} chapters, {words} words.",
    ]
    if missing:
        header.append("Skipped missing chapters: " + ", ".join(missing) + ".")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(header) + "\n\n" + "\n\n".join(parts) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
