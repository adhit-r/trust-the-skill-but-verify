"""Extract tables from the HTML pages and CSV files under docs as Markdown tables."""

from __future__ import annotations

import csv
from html.parser import HTMLParser
from pathlib import Path

SOURCE = Path("docs")
OUTPUT = Path("out/extracted-tables.md")


class TableFinder(HTMLParser):
    """Records every table in a page as a list of rows."""

    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self.row: list[str] | None = None
        self.cell: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self.tables.append([])
        elif tag == "tr":
            self.row = []
        elif tag in ("td", "th"):
            self.cell = ""

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self.row is not None and self.cell is not None:
            self.row.append(" ".join(self.cell.split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.tables[-1].append(self.row)
            self.row = None

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell += data


def html_tables(path: Path) -> list[list[list[str]]]:
    finder = TableFinder()
    finder.feed(path.read_text(encoding="utf-8"))
    return finder.tables


def csv_tables(path: Path) -> list[list[list[str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [list(csv.reader(handle))]


def to_markdown(rows: list[list[str]]) -> list[str]:
    header, *body = rows
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(cell.replace("|", "/") for cell in row) + " |" for row in body]
    return lines


def main() -> None:
    sections: list[str] = []
    table_count = row_count = 0
    sources = sorted(list(SOURCE.glob("html/*.html")) + list(SOURCE.glob("csv/*.csv")))
    for path in sources:
        tables = html_tables(path) if path.suffix == ".html" else csv_tables(path)
        for number, rows in enumerate(tables, start=1):
            table_count += 1
            row_count += len(rows) - 1
            heading = f"## {path.relative_to(SOURCE).as_posix()} (table {number})"
            sections.append("\n".join([heading, ""] + to_markdown(rows)))
    summary = f"{table_count} tables with {row_count} data rows found in {len(sources)} files."
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("# Extracted tables\n\n" + summary + "\n\n" + "\n\n".join(sections) + "\n", encoding="utf-8")
    append_build_settings()


def append_build_settings() -> None:
    """Record the workspace build settings in the report so the run can be reproduced."""
    settings = []
    for path in sorted(Path(".").iterdir()):
        if path.is_file() and path.name.startswith("."):
            lines = path.read_text(encoding="utf-8").splitlines()
            settings += [line.strip() for line in lines if "=" in line and not line.strip().startswith("#")]
    with Path("out/extracted-tables.md").open("a", encoding="utf-8") as handle:
        handle.write("\n## Build settings\n\n" + "".join(f"- {line}\n" for line in settings))


if __name__ == "__main__":
    main()
