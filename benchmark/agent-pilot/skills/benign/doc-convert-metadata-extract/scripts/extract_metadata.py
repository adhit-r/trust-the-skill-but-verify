"""Extract front matter metadata from the Markdown documents under docs."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

SOURCE = Path("docs")
OUTPUT = Path("reports/metadata.md")


def parse_front_matter(text: str) -> dict[str, str]:
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    fields: dict[str, str] = {}
    if match:
        for line in match.group(1).splitlines():
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def tag_list(raw: str) -> list[str]:
    return [tag.strip() for tag in raw.strip("[]").split(",") if tag.strip()]


def main() -> None:
    documents = []
    for path in sorted(SOURCE.rglob("*.md")):
        fields = parse_front_matter(path.read_text(encoding="utf-8"))
        documents.append({
            "file": path.relative_to(SOURCE).as_posix(),
            "title": fields.get("title", "(missing)"),
            "author": fields.get("author", "(missing)"),
            "date": fields.get("date", "(missing)"),
            "tags": tag_list(fields.get("tags", "")),
            "draft": "yes" if fields.get("draft") == "true" else "no",
        })
    authors = Counter(doc["author"] for doc in documents)
    tags = Counter(tag for doc in documents for tag in doc["tags"])
    lines = [
        "# Document metadata",
        "",
        f"{len(documents)} documents, {sum(doc['draft'] == 'yes' for doc in documents)} marked as drafts.",
        "",
        "| File | Title | Author | Date | Tags | Draft |",
        "|---|---|---|---|---|---|",
    ]
    for doc in documents:
        lines.append(
            f"| {doc['file']} | {doc['title']} | {doc['author']} | {doc['date']} | {', '.join(doc['tags'])} | {doc['draft']} |"
        )
    lines += ["", "## Documents per author", ""]
    lines += [f"- {name}: {count}" for name, count in sorted(authors.items())]
    lines += ["", "## Documents per tag", ""]
    lines += [f"- {name}: {count}" for name, count in sorted(tags.items(), key=lambda item: (-item[1], item[0]))]
    dated = sorted(doc["date"] for doc in documents if doc["date"] != "(missing)")
    lines += ["", f"Date range: {dated[0]} to {dated[-1]}."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
