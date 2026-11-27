"""Split the corpus documents into retrieval chunks that respect the word limits in rules/chunking.json."""

from __future__ import annotations

import json
import re
from pathlib import Path

CORPUS = Path("corpus")
OUTPUT = Path("reports/chunks.md")
BULLET = re.compile(r"^(?:[-*]|\d+\.)\s+")


def sections(text: str) -> list[tuple[str, list[str]]]:
    """Return (heading, blocks) pairs, where each block is a paragraph or list item."""
    result: list[tuple[str, list[str]]] = [("", [])]
    paragraph: list[str] = []
    for line in text.splitlines() + [""]:
        heading = re.match(r"^#{1,6}\s+(.*)$", line)
        if heading or not line.strip() or BULLET.match(line):
            if paragraph:
                result[-1][1].append(" ".join(paragraph))
                paragraph = []
            if heading:
                result.append((heading.group(1), []))
            elif BULLET.match(line):
                result[-1][1].append(BULLET.sub("", line))
        else:
            paragraph.append(line.strip())
    return [(title, blocks) for title, blocks in result if blocks]


def chunk_section(blocks: list[str], limit: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    for block in blocks:
        if current and len(" ".join(current + [block]).split()) > limit:
            chunks.append(" ".join(current))
            current = []
        current.append(block)
    if current:
        chunks.append(" ".join(current))
    return chunks


def main() -> None:
    rules = json.loads((CORPUS / "rules" / "chunking.json").read_text(encoding="utf-8"))
    rows = []
    for path in sorted(CORPUS.glob("*/*.md")):
        for title, blocks in sections(path.read_text(encoding="utf-8")):
            for body in chunk_section(blocks, rules["max_words"]):
                text = f"{title}: {body}" if rules["carry_heading"] and title else body
                rows.append((path.stem, len(text.split()), text))
    short = [row for row in rows if row[1] < rules["min_words"]]
    lines = [
        "# Retrieval chunks",
        "",
        f"{len(rows)} chunks with a limit of {rules['max_words']} words; {len(short)} are shorter than {rules['min_words']} words.",
        "",
        "| Chunk | Document | Words | Text |",
        "|---|---|---|---|",
    ]
    for number, (stem, words, text) in enumerate(rows, start=1):
        flag = " (short)" if words < rules["min_words"] else ""
        lines.append(f"| {number:03d} | {stem} | {words}{flag} | {text} |")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
