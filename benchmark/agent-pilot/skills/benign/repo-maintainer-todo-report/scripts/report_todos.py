"""Collect TODO and FIXME comments from the repository into a report."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

REPO = Path("repo")
OUTPUT = Path("reports/todo-report.md")
SOURCE_SUFFIXES = {".py", ".js"}
PATTERN = re.compile(r"\b(TODO|FIXME)(?:\(([\w-]+)\))?:?\s*(.*)")


def find_markers() -> list[dict[str, str]]:
    markers = []
    for path in sorted(REPO.rglob("*")):
        if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines, start=1):
            match = PATTERN.search(line)
            if match:
                kind, author, note = match.groups()
                markers.append({
                    "file": path.relative_to(REPO).as_posix(),
                    "line": str(number),
                    "kind": kind,
                    "author": author or "-",
                    "note": note.strip(),
                })
    return markers


def render(markers: list[dict[str, str]]) -> str:
    kinds = Counter(marker["kind"] for marker in markers)
    areas = Counter(marker["file"].split("/")[0] for marker in markers)
    lines = [
        "# TODO and FIXME report",
        "",
        f"{len(markers)} markers: {kinds['FIXME']} FIXME, {kinds['TODO']} TODO.",
        "",
        "## By area",
        "",
    ]
    lines += [f"- {area}: {count}" for area, count in sorted(areas.items())]
    lines += ["", "## Markers", "", "| Location | Kind | Author | Note |", "|---|---|---|---|"]
    ordered = sorted(markers, key=lambda m: (m["kind"] != "FIXME", m["file"], int(m["line"])))
    for marker in ordered:
        lines.append(f"| {marker['file']}:{marker['line']} | {marker['kind']} | {marker['author']} | {marker['note']} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    markers = find_markers()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(markers), encoding="utf-8")


if __name__ == "__main__":
    main()
