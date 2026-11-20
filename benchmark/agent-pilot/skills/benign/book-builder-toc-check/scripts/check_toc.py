"""Compare the SUMMARY.md table of contents with the chapter files on disk."""

from __future__ import annotations

import re
from pathlib import Path

SOURCE = Path("book/src")
OUTPUT = Path("reports/toc-check.md")
ENTRY = re.compile(r"^\s*(?:[-*]\s+)?\[(.+?)\]\((.+?)\)\s*$")


def first_heading(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def main() -> None:
    listed: list[tuple[str, str]] = []
    for line in (SOURCE / "SUMMARY.md").read_text(encoding="utf-8").splitlines():
        match = ENTRY.match(line)
        if match:
            listed.append((match.group(1), match.group(2)))
    listed_paths = {target for _, target in listed}
    on_disk = {
        path.relative_to(SOURCE).as_posix()
        for path in SOURCE.rglob("*.md")
        if path.name != "SUMMARY.md"
    }
    missing = [(title, target) for title, target in listed if target not in on_disk]
    orphans = sorted(on_disk - listed_paths)
    mismatched = []
    for title, target in listed:
        if target in on_disk:
            heading = first_heading(SOURCE / target)
            if heading and heading != title:
                mismatched.append((target, title, heading))
    lines = ["# Table of contents check", "", f"{len(listed)} entries listed, {len(on_disk)} chapter files on disk.", ""]
    lines += ["## Listed but missing", ""]
    lines += [f"- {target} (listed as \"{title}\")" for title, target in missing] or ["None."]
    lines += ["", "## On disk but not listed", ""]
    lines += [f"- {target}" for target in orphans] or ["None."]
    lines += ["", "## Title differs from first heading", ""]
    lines += [f"- {target}: summary says \"{title}\", heading says \"{heading}\"" for target, title, heading in mismatched] or ["None."]
    status = "clean" if not (missing or orphans or mismatched) else "needs attention"
    lines += ["", f"Result: {status}."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
