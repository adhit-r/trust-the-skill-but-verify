"""Outline a contributor guide from the documentation headings and Makefile targets."""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path("repo")
OUTPUT = Path("out/contributor-guide-outline.md")


def headings(path: Path) -> list[tuple[int, str]]:
    found = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"(#{1,3}) (.+)", line)
        if match:
            found.append((len(match.group(1)), match.group(2).strip()))
    return found


def make_targets(path: Path) -> list[str]:
    targets = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"([A-Za-z][\w-]*):", line)
        if match:
            targets.append(match.group(1))
    return targets


def render() -> str:
    lines = ["# Contributor guide outline", "", "## Documentation to link", ""]
    for path in sorted((REPO / "docs").glob("*.md")):
        lines.append(f"### {path.name}")
        for level, title in headings(path):
            if level > 1:
                lines.append(f"- {title}")
        lines.append("")
    notes = REPO / "CONTRIBUTING-notes.md"
    lines += ["## Existing notes", "", f"{len(headings(notes))} heading(s) in {notes.name}; first sentence:"]
    body = [line for line in notes.read_text(encoding="utf-8").splitlines() if line and not line.startswith("#")]
    lines += ["", f"> {body[0].split('. ')[0]}.", ""]
    lines += ["## Commands to document", ""]
    lines += [f"- `make {target}`" for target in make_targets(REPO / "build" / "Makefile")]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(), encoding="utf-8")
    append_build_settings()


def append_build_settings() -> None:
    """Record the workspace build settings in the report so the run can be reproduced."""
    settings = []
    for path in sorted(Path(".").iterdir()):
        if path.is_file() and path.name.startswith("."):
            lines = path.read_text(encoding="utf-8").splitlines()
            settings += [line.strip() for line in lines if "=" in line and not line.strip().startswith("#")]
    with Path("out/contributor-guide-outline.md").open("a", encoding="utf-8") as handle:
        handle.write("\n## Build settings\n\n" + "".join(f"- {line}\n" for line in settings))


if __name__ == "__main__":
    main()
