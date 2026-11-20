"""Index every document under docs with format, size, line count and title."""

from __future__ import annotations

import csv
import re
from pathlib import Path

SOURCE = Path("docs")
OUTPUT = Path("reports/conversion-index.md")


def html_title(text: str) -> str:
    match = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.S) or re.search(r"<title>(.*?)</title>", text, re.S)
    return " ".join(match.group(1).split()) if match else "(untitled)"


def csv_shape(path: Path) -> tuple[int, int]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    return max(len(rows) - 1, 0), len(rows[0]) if rows else 0


def describe(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lstrip(".")
    entry = {
        "file": path.relative_to(SOURCE).as_posix(),
        "format": suffix,
        "bytes": str(len(text.encode("utf-8"))),
        "lines": str(len(text.splitlines())),
        "title": "",
        "shape": "-",
    }
    if suffix == "html":
        entry["title"] = html_title(text)
    elif suffix == "csv":
        rows, columns = csv_shape(path)
        entry["title"] = path.stem.replace("-", " ").title()
        entry["shape"] = f"{rows} rows x {columns} columns"
    else:
        entry["title"] = text.splitlines()[0].strip() if text.strip() else "(empty)"
    return entry


def main() -> None:
    entries = [describe(path) for path in sorted(SOURCE.rglob("*")) if path.is_file()]
    by_format: dict[str, int] = {}
    for entry in entries:
        by_format[entry["format"]] = by_format.get(entry["format"], 0) + 1
    total = sum(int(entry["bytes"]) for entry in entries)
    lines = [
        "# Conversion index",
        "",
        f"{len(entries)} documents, {total} bytes in total.",
        "",
        "| File | Format | Bytes | Lines | Title | Table shape |",
        "|---|---|---|---|---|---|",
    ]
    for entry in entries:
        lines.append(
            f"| {entry['file']} | {entry['format']} | {entry['bytes']} | {entry['lines']} | {entry['title']} | {entry['shape']} |"
        )
    lines += ["", "## Formats", ""]
    lines += [f"- {name}: {count}" for name, count in sorted(by_format.items())]
    largest = max(entries, key=lambda item: int(item["bytes"]))
    lines += ["", f"Largest document: {largest['file']} ({largest['bytes']} bytes)."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
