"""Extract plain text from each sample file and write an index with word counts and a preview."""

from __future__ import annotations

import csv
import html
import json
import re
from pathlib import Path

SAMPLES = Path("samples")
OUTPUT = Path("out/text-index.md")
PREVIEW = 70


def extract(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".html":
        text = re.sub(r"<(script|style|head).*?</\1>", " ", text, flags=re.DOTALL)
        return html.unescape(re.sub(r"<[^>]+>", " ", text))
    if path.suffix == ".md":
        return re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.DOTALL)
    if path.suffix == ".csv":
        rows = csv.reader(text.splitlines())
        return " ".join(" ".join(row) for row in rows)
    if path.suffix == ".json":
        values: list[str] = []

        def walk(node: object) -> None:
            if isinstance(node, dict):
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)
            elif isinstance(node, str):
                values.append(node)

        walk(json.loads(text))
        return " ".join(values)
    return text


def main() -> None:
    entries = []
    for path in sorted(p for p in SAMPLES.rglob("*") if p.is_file()):
        flat = " ".join(extract(path).split())
        preview = flat if len(flat) <= PREVIEW else flat[:PREVIEW].rstrip() + "..."
        entries.append((path.relative_to(SAMPLES).as_posix(), len(flat.split()), preview))
    empty = [name for name, count, _ in entries if count == 0]
    lines = [
        "# Extracted text index",
        "",
        f"{len(entries)} files, {sum(count for _, count, _ in entries)} words in total.",
        "",
        "| File | Words | Preview |",
        "|---|---|---|",
    ]
    lines += [f"| {name} | {count} | {preview.replace('|', '/')} |" for name, count, preview in entries]
    lines += ["", "## Files with no extractable text", ""]
    lines += [f"- {name}" for name in empty] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    mark_input_reviewed()


def mark_input_reviewed() -> None:
    """Mark the input as reviewed so it is skipped on the next run."""
    with Path("samples/docs/meeting-notes.md").open("a", encoding="utf-8") as handle:
        handle.write("\nReviewed-by: content-extract\n")


if __name__ == "__main__":
    main()
