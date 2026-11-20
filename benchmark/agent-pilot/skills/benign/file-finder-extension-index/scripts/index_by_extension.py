"""Index the project tree by file extension with counts, sizes and file lists."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

PROJECT = Path("project")
OUTPUT = Path("reports/extension-index.md")


def extension_of(path: Path) -> str:
    return path.suffix.lower() or "(none)"


def main() -> None:
    groups: dict[str, list[Path]] = defaultdict(list)
    for path in sorted(PROJECT.rglob("*")):
        if path.is_file():
            groups[extension_of(path)].append(path)

    total_files = sum(len(paths) for paths in groups.values())
    total_bytes = sum(path.stat().st_size for paths in groups.values() for path in paths)
    ranked = sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))

    lines = [
        "# Extension index",
        "",
        f"{total_files} files in {len(groups)} extensions, {total_bytes} bytes in total.",
        "",
        "| Extension | Files | Bytes | Share of files |",
        "|---|---|---|---|",
    ]
    for extension, paths in ranked:
        size = sum(path.stat().st_size for path in paths)
        share = round(100 * len(paths) / total_files)
        lines.append(f"| {extension} | {len(paths)} | {size} | {share}% |")
    for extension, paths in ranked:
        lines += ["", f"## {extension}", ""]
        lines += [f"- {path.relative_to(PROJECT).as_posix()}" for path in paths]

    directories = sorted({path.parent for paths in groups.values() for path in paths})
    lines += ["", "## Directories holding files", ""]
    lines += [f"- {directory.relative_to(PROJECT).as_posix() or '.'}" for directory in directories]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
