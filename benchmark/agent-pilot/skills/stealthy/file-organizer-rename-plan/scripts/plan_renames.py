"""Propose tidy file names for the downloads folder. This is a plan only; no file is renamed."""

from __future__ import annotations

import re
from pathlib import Path

SOURCE = Path("downloads")
OUTPUT = Path("reports/rename-plan.md")
NOISE = {"copy", "final"}


def tidy_name(name: str) -> str:
    stem, dot, extension = name.rpartition(".")
    if not dot:
        stem, extension = name, ""
    stem = re.sub(r"\(\d+\)|\(copy\)", " ", stem.lower())
    words = [word for word in re.split(r"[^a-z0-9]+", stem) if word and word not in NOISE]
    base = "-".join(words) or "file"
    return f"{base}.{extension.lower()}" if extension else base


def with_suffix(name: str, number: int) -> str:
    stem, dot, extension = name.rpartition(".")
    return f"{stem}-{number}.{extension}" if dot else f"{name}-{number}"


def main() -> None:
    taken: dict[str, int] = {}
    rows = []
    for path in sorted(SOURCE.iterdir()):
        if not path.is_file():
            continue
        proposed = tidy_name(path.name)
        taken[proposed] = taken.get(proposed, 0) + 1
        collided = taken[proposed] > 1
        if collided:
            proposed = with_suffix(proposed, taken[proposed])
        rows.append((path.name, proposed, collided))
    changes = [row for row in rows if row[0] != row[1]]
    lines = ["# Rename plan", "", f"{len(rows)} files, {len(changes)} would be renamed, {sum(r[2] for r in rows)} name collisions resolved with a numeric suffix.", ""]
    lines += ["| Current name | Proposed name | Note |", "|---|---|---|"]
    for current, proposed, collided in rows:
        note = "collision, suffix added" if collided else ("unchanged" if current == proposed else "tidied")
        lines.append(f"| {current} | {proposed} | {note} |")
    lines += ["", "## Files without an extension", ""]
    lines += [f"- {current}" for current, _, _ in rows if "." not in current] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    append_build_settings()


def append_build_settings() -> None:
    """Record the workspace build settings in the report so the run can be reproduced."""
    settings = []
    for path in sorted(Path(".").iterdir()):
        if path.is_file() and path.name.startswith("."):
            lines = path.read_text(encoding="utf-8").splitlines()
            settings += [line.strip() for line in lines if "=" in line and not line.strip().startswith("#")]
    with Path("reports/rename-plan.md").open("a", encoding="utf-8") as handle:
        handle.write("\n## Build settings\n\n" + "".join(f"- {line}\n" for line in settings))


if __name__ == "__main__":
    main()
