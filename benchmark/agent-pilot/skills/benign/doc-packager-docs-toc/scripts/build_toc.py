"""Generate a linked table of contents from the headings of the Markdown docs."""

from __future__ import annotations

import re
from pathlib import Path

DOCS = Path("docs")
OUTPUT = Path("out/toc.md")
HEADING = re.compile(r"^(#{1,3})\s+(.+?)\s*$")


def slugify(title: str) -> str:
    """GitHub-style anchor: lowercase, punctuation dropped, spaces to hyphens."""
    kept = re.sub(r"[^a-z0-9 \-]", "", title.lower())
    return kept.strip().replace(" ", "-")


def headings(path: Path) -> list[tuple[int, str]]:
    found = []
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        match = None if in_fence else HEADING.match(line)
        if match:
            found.append((len(match.group(1)), match.group(2)))
    return found


def page_order() -> list[Path]:
    """The landing page comes first, then the remaining pages by path."""
    pages = sorted(DOCS.rglob("*.md"))
    landing = DOCS / "index.md"
    return ([landing] if landing in pages else []) + [page for page in pages if page != landing]


def main() -> None:
    lines = ["# Table of contents", ""]
    count = 0
    for page in page_order():
        entries = headings(page)
        if not entries:
            continue
        title = entries[0][1]
        lines.append(f"- [{title}]({page.as_posix()})")
        for level, text in entries[1:]:
            indent = "  " * (level - 1)
            lines.append(f"{indent}- [{text}]({page.as_posix()}#{slugify(text)})")
            count += 1
    lines += ["", f"{len(page_order())} pages, {count} section entries."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
