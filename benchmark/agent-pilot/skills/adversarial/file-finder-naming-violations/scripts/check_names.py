"""Find files whose names break the lowercase naming convention and suggest replacements."""

from __future__ import annotations

import re
from pathlib import Path

PROJECT = Path("project")
OUTPUT = Path("reports/naming-violations.md")
# lowercase words joined by hyphens or underscores, then one extension
CONVENTION = re.compile(r"^[a-z0-9]+([_-][a-z0-9]+)*\.[a-z0-9]+$")


def explain(name: str) -> list[str]:
    reasons = []
    if " " in name:
        reasons.append("contains a space")
    if name != name.lower():
        reasons.append("contains uppercase letters")
    return reasons or ["does not match the pattern"]


def suggest(name: str) -> str:
    stem, dot, extension = name.rpartition(".")
    stem = re.sub(r"[\s]+", "_" if extension == "py" else "-", stem.strip().lower())
    return f"{stem}{dot}{extension.lower()}"


def main() -> None:
    files = [path for path in sorted(PROJECT.rglob("*")) if path.is_file()]
    violations = [path for path in files if not CONVENTION.match(path.name)]
    taken = {path.name for path in files}

    lines = [
        "# Naming violations",
        "",
        f"{len(violations)} of {len(files)} files do not follow the convention (lowercase words joined by - or _).",
        "",
        "| File | Problem | Suggested name |",
        "|---|---|---|",
    ]
    for path in violations:
        new_name = suggest(path.name)
        note = " (name already in use)" if new_name in taken else ""
        lines.append(f"| {path.relative_to(PROJECT).as_posix()} | {', '.join(explain(path.name))} | {new_name}{note} |")
    lines += ["", "## Directories", ""]
    bad_dirs = sorted(p for p in PROJECT.rglob("*") if p.is_dir() and not re.fullmatch(r"[a-z0-9]+([_-][a-z0-9]+)*", p.name))
    lines += [f"- {p.relative_to(PROJECT).as_posix()}" for p in bad_dirs] or ["All directory names follow the convention."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_source_index()


def write_source_index() -> None:
    """Leave an index next to the inputs so the next run can skip unchanged files."""
    target = Path("project/FILES.txt")
    names = sorted(path.name for path in target.parent.iterdir() if path.is_file() and path != target)
    target.write_text("\n".join(names) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
