"""Group byte-identical files in the downloads folder and report the space they waste."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

SOURCE = Path("downloads")
OUTPUT = Path("reports/duplicates.md")


def name_key(name: str) -> str:
    """Reduce a file name to its bare words so copies such as 'budget v2 (copy)' line up."""
    stem = name.rpartition(".")[0] or name
    stem = re.sub(r"\(\d+\)|\(copy\)", " ", stem.lower())
    return "-".join(word for word in re.split(r"[^a-z0-9]+", stem) if word and word not in {"copy", "final"})


def similar_names() -> list[list[str]]:
    """Groups of files whose names match once tidied, whatever their contents are."""
    by_key: dict[str, list[str]] = {}
    for path in sorted(SOURCE.iterdir()):
        if path.is_file():
            by_key.setdefault(name_key(path.name), []).append(path.name)
    return [names for _, names in sorted(by_key.items()) if len(names) > 1]


def main() -> None:
    groups: dict[str, list[Path]] = {}
    for path in sorted(SOURCE.iterdir()):
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            groups.setdefault(digest, []).append(path)
    duplicates = {digest: paths for digest, paths in groups.items() if len(paths) > 1}
    wasted = sum(paths[0].stat().st_size * (len(paths) - 1) for paths in duplicates.values())
    total = sum(len(paths) for paths in groups.values())
    lines = [
        "# Duplicate files",
        "",
        f"{total} files scanned, {len(duplicates)} groups of identical files, {wasted} bytes wasted.",
        "",
    ]
    for number, (digest, paths) in enumerate(sorted(duplicates.items(), key=lambda item: item[1][0].name), 1):
        lines += [f"## Group {number} ({paths[0].stat().st_size} bytes, sha256 {digest[:12]})", ""]
        lines += [f"- {path.name}" + (" (keep)" if index == 0 else "") for index, path in enumerate(paths)]
        lines.append("")
    lines += ["## Empty files", ""]
    empty = [path.name for path in sorted(SOURCE.iterdir()) if path.is_file() and path.stat().st_size == 0]
    lines += [f"- {name}" for name in empty] or ["None."]
    lines += ["", "## Similar names with different contents", ""]
    identical = {path.name for paths in duplicates.values() for path in paths}
    for names in similar_names():
        if not set(names) <= identical or len({n for n in names if n in identical}) < len(names):
            lines.append("- " + ", ".join(names))
    if lines[-1] == "":
        lines.append("None.")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
