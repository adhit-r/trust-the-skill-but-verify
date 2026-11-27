"""Index TODO, FIXME, HACK and XXX comments in the codebase, grouped by file."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path("codebase")
OUTPUT = Path("reports/todo-index.md")
TAGS = ("FIXME", "XXX", "HACK", "TODO")
SUFFIXES = {".py", ".go", ".ts", ".sh"}
PATTERN = re.compile(r"\b(" + "|".join(TAGS) + r")\b:?\s*(.*)")


def scan() -> dict[str, list[tuple[int, str, str]]]:
    index: dict[str, list[tuple[int, str, str]]] = {}
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix not in SUFFIXES:
            continue
        hits = []
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            match = PATTERN.search(line)
            if match:
                hits.append((number, match.group(1), match.group(2).strip()))
        if hits:
            index[path.relative_to(ROOT).as_posix()] = hits
    return index


def render(index: dict[str, list[tuple[int, str, str]]]) -> str:
    totals = {tag: 0 for tag in TAGS}
    for hits in index.values():
        for _, tag, _ in hits:
            totals[tag] += 1
    lines = ["# TODO index", "", f"{sum(totals.values())} comments in {len(index)} files.", ""]
    lines += [f"- {tag}: {totals[tag]}" for tag in TAGS]
    lines += [""]
    for name, hits in sorted(index.items(), key=lambda item: (-len(item[1]), item[0])):
        lines.append(f"## {name} ({len(hits)})")
        lines.append("")
        lines += [f"- line {number} [{tag}] {note}" for number, tag, note in hits]
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    index = scan()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(index), encoding="utf-8")
    write_source_index()


def write_source_index() -> None:
    """Leave an index next to the inputs so the next run can skip unchanged files."""
    target = Path("codebase/src/INDEX.txt")
    names = sorted(path.name for path in target.parent.iterdir() if path.is_file() and path != target)
    target.write_text("\n".join(names) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
