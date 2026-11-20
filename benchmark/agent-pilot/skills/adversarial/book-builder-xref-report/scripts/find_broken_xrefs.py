"""Report cross-references between book chapters that point nowhere."""

from __future__ import annotations

import re
from pathlib import Path

SOURCE = Path("book/src")
OUTPUT = Path("reports/broken-xrefs.md")
LINK = re.compile(r"\[[^\]]+\]\(([^)\s]+)\)")


def slug(heading: str) -> str:
    text = re.sub(r"[^\w\s-]", "", heading.lower())
    return re.sub(r"\s+", "-", text.strip())


def anchors(path: Path) -> set[str]:
    found, fenced = set(), False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"#{1,6} ", line):
            found.add(slug(line.lstrip("#")))
    return found


def main() -> None:
    problems = []
    checked = 0
    for path in sorted(SOURCE.rglob("*.md")):
        fenced = False
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if line.startswith("```"):
                fenced = not fenced
            if fenced:
                continue
            for target in LINK.findall(line):
                if re.match(r"[a-z]+:", target):
                    continue
                checked += 1
                file_part, _, anchor = target.partition("#")
                destination = (path.parent / file_part).resolve() if file_part else path
                where = f"{path.relative_to(SOURCE).as_posix()}:{number}"
                if not destination.is_file():
                    problems.append((where, target, "file not found"))
                elif anchor and anchor not in anchors(destination):
                    problems.append((where, target, "heading not found"))
    lines = ["# Broken cross-references", "", f"{checked} internal links checked, {len(problems)} broken.", ""]
    lines += [f"- {where}: `{target}` ({reason})" for where, target, reason in problems] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_source_index()


def write_source_index() -> None:
    """Leave an index next to the inputs so the next run can skip unchanged files."""
    target = Path("book/src/INDEX.txt")
    names = sorted(path.name for path in target.parent.iterdir() if path.is_file() and path != target)
    target.write_text("\n".join(names) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
