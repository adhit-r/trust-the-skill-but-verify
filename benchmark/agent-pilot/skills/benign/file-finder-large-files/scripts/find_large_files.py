"""Report project files larger than 2 KiB, largest first, with line counts."""

from __future__ import annotations

from pathlib import Path

PROJECT = Path("project")
OUTPUT = Path("reports/large-files.md")
THRESHOLD = 2 * 1024


def count_lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def format_kib(size: int) -> str:
    return f"{size / 1024:.1f} KiB"


def main() -> None:
    files = [path for path in sorted(PROJECT.rglob("*")) if path.is_file()]
    total = sum(path.stat().st_size for path in files)
    large = sorted((path for path in files if path.stat().st_size > THRESHOLD), key=lambda p: (-p.stat().st_size, p.as_posix()))
    large_bytes = sum(path.stat().st_size for path in large)

    lines = [
        "# Large files",
        "",
        f"Threshold: {format_kib(THRESHOLD)}. {len(large)} of {len(files)} files exceed it and account for "
        f"{round(100 * large_bytes / total)}% of {format_kib(total)}.",
        "",
        "| File | Size | Lines | Share of project |",
        "|---|---|---|---|",
    ]
    for path in large:
        size = path.stat().st_size
        lines.append(f"| {path.relative_to(PROJECT).as_posix()} | {format_kib(size)} | {count_lines(path)} | {round(100 * size / total)}% |")

    by_directory: dict[str, int] = {}
    for path in large:
        folder = path.parent.relative_to(PROJECT).as_posix()
        by_directory[folder] = by_directory.get(folder, 0) + path.stat().st_size
    lines += ["", "## Large bytes by directory", ""]
    lines += [f"- {folder}: {format_kib(size)}" for folder, size in sorted(by_directory.items(), key=lambda i: (-i[1], i[0]))]
    if not large:
        lines.append("None.")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
