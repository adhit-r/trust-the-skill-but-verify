"""Check internal Markdown links and heading anchors across the docs folder."""

from __future__ import annotations

import re
from pathlib import Path

DOCS = Path("docs")
OUTPUT = Path("reports/link-check.md")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$")


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9 \-]", "", title.lower()).strip().replace(" ", "-")


def body_lines(path: Path) -> list[str]:
    """Lines outside fenced code blocks."""
    lines, in_fence = [], False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
        elif not in_fence:
            lines.append(line)
    return lines


def anchors(path: Path) -> set[str]:
    return {slugify(m.group(1)) for line in body_lines(path) if (m := HEADING.match(line))}


def check(page: Path, target: str) -> str | None:
    """Return a problem description for a link, or None if it resolves."""
    path_part, _, fragment = target.partition("#")
    destination = page if not path_part else (page.parent / path_part).resolve()
    if path_part and not destination.is_file():
        return "file not found"
    if fragment and fragment not in anchors(destination):
        return f"no heading with anchor #{fragment}"
    return None


def main() -> None:
    checked = 0
    problems: list[tuple[str, str, str]] = []
    for page in sorted(DOCS.rglob("*.md")):
        for line in body_lines(page):
            for target in LINK.findall(line):
                if re.match(r"[a-z]+:", target):
                    continue
                checked += 1
                problem = check(page, target)
                if problem:
                    problems.append((page.relative_to(DOCS).as_posix(), target, problem))
    out = ["# Link check", "", f"Checked {checked} internal links; {len(problems)} are broken.", "", "## Broken links", ""]
    if problems:
        out += ["| Page | Link | Problem |", "|---|---|---|"]
        out += [f"| {page} | {target} | {problem} |" for page, target, problem in problems]
    else:
        out.append("None.")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
