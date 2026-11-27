"""Outline the heading hierarchy of each corpus document and flag skipped heading levels."""

from __future__ import annotations

import re
from pathlib import Path

CORPUS = Path("corpus")
OUTPUT = Path("reports/heading-hierarchy.md")


def headings(path: Path) -> list[tuple[int, str]]:
    found = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if match:
            found.append((len(match.group(1)), match.group(2).strip()))
    return found


def main() -> None:
    lines = ["# Heading hierarchy", ""]
    problems = []
    total = 0
    for path in sorted(CORPUS.glob("*/*.md")):
        found = headings(path)
        total += len(found)
        deepest = max((level for level, _ in found), default=0)
        lines += [f"## {path.relative_to(CORPUS).as_posix()}", "", f"{len(found)} headings, deepest level {deepest}.", ""]
        previous = 0
        for level, title in found:
            lines.append(f"{'  ' * (level - 1)}- {title} (h{level})")
            if level > previous + 1:
                problems.append(f"{path.name}: '{title}' jumps from h{previous} to h{level}")
            previous = level
        lines.append("")
    lines += ["## Level skips", ""]
    lines += [f"- {problem}" for problem in problems] or ["None."]
    lines += ["", f"Total headings: {total}."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
