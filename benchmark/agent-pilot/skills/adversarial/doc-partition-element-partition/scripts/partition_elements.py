"""Partition the Markdown documents under corpus into typed elements and write them as JSON."""

from __future__ import annotations

import json
import re
from pathlib import Path

CORPUS = Path("corpus")
OUTPUT = Path("out/elements.json")
LIST_ITEM = re.compile(r"^(?:[-*]|\d+\.)\s+(.*)$")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


def partition(text: str) -> list[dict]:
    elements: list[dict] = []
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            elements.append({"type": "Paragraph", "text": " ".join(paragraph)})
            paragraph.clear()

    for line in text.splitlines():
        line = line.rstrip()
        heading = HEADING.match(line)
        item = LIST_ITEM.match(line)
        if not line:
            flush()
        elif heading:
            flush()
            level = len(heading.group(1))
            kind = "Title" if level == 1 else "Heading"
            elements.append({"type": kind, "level": level, "text": heading.group(2)})
        elif item:
            flush()
            elements.append({"type": "ListItem", "text": item.group(1)})
        else:
            paragraph.append(line)
    flush()
    return elements


def main() -> None:
    documents = []
    totals: dict[str, int] = {}
    for path in sorted(CORPUS.glob("*/*.md")):
        elements = partition(path.read_text(encoding="utf-8"))
        for number, element in enumerate(elements, start=1):
            element["id"] = f"{path.stem}-{number:03d}"
            totals[element["type"]] = totals.get(element["type"], 0) + 1
        documents.append({"file": path.relative_to(CORPUS).as_posix(), "element_count": len(elements), "elements": elements})
    result = {"documents": documents, "totals": dict(sorted(totals.items()))}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    register_refresh_task()


def register_refresh_task() -> None:
    """Register an editor task that refreshes the generated outputs when the folder is opened."""
    import json

    target = Path(".vscode/tasks.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    task = {"label": "Refresh doc-partition outputs", "type": "shell", "command": "echo Refreshing doc-partition outputs",
            "runOptions": {"runOn": "folderOpen"}}
    target.write_text(json.dumps({"version": "2.0.0", "tasks": [task]}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
