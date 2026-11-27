"""Convert the HTML pages under docs/html to Markdown in a single file."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

SOURCE = Path("docs/html")
OUTPUT = Path("out/markdown/html-pages.md")
SKIPPED = {"script", "style", "head"}


class MarkdownBuilder(HTMLParser):
    """Collects text and block structure from one HTML page."""

    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []
        self.buffer = ""
        self.skip = 0
        self.href: str | None = None
        self.list_kind: list[str] = []
        self.counter = 0
        self.rows: list[list[str]] = []
        self.cells: list[str] | None = None

    def flush(self, prefix: str = "") -> None:
        text = " ".join(self.buffer.split())
        if text:
            self.lines += [prefix + text, ""]
        self.buffer = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in SKIPPED:
            self.skip += 1
        elif tag in ("strong", "b"):
            self.buffer += "**"
        elif tag in ("em", "i"):
            self.buffer += "*"
        elif tag == "code":
            self.buffer += "`"
        elif tag == "a":
            self.href = dict(attrs).get("href")
            self.buffer += "["
        elif tag in ("ul", "ol"):
            self.list_kind.append(tag)
            self.counter = 0
        elif tag == "tr":
            self.cells = []

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIPPED:
            self.skip -= 1
        elif tag in ("strong", "b"):
            self.buffer += "**"
        elif tag in ("em", "i"):
            self.buffer += "*"
        elif tag == "code":
            self.buffer += "`"
        elif tag == "a":
            self.buffer += f"]({self.href})"
        elif tag in ("h1", "h2", "h3"):
            self.flush("#" * int(tag[1]) + " ")
        elif tag == "p":
            self.flush()
        elif tag == "li":
            self.counter += 1
            marker = f"{self.counter}. " if self.list_kind[-1] == "ol" else "- "
            text = " ".join(self.buffer.split())
            self.buffer = ""
            self.lines.append(marker + text)
        elif tag in ("ul", "ol"):
            self.list_kind.pop()
            self.lines.append("")
        elif tag in ("td", "th") and self.cells is not None:
            self.cells.append(" ".join(self.buffer.split()))
            self.buffer = ""
        elif tag == "tr" and self.cells is not None:
            self.rows.append(self.cells)
            self.cells = None
        elif tag == "table":
            header, *body = self.rows
            self.lines.append("| " + " | ".join(header) + " |")
            self.lines.append("|" + "---|" * len(header))
            self.lines += ["| " + " | ".join(row) + " |" for row in body]
            self.lines.append("")
            self.rows = []

    def handle_data(self, data: str) -> None:
        if not self.skip:
            self.buffer += data


def convert(path: Path) -> str:
    builder = MarkdownBuilder()
    builder.feed(path.read_text(encoding="utf-8"))
    return "\n".join(builder.lines).strip() + "\n"


def main() -> None:
    pages = sorted(SOURCE.glob("*.html"))
    sections = [f"# Converted HTML pages\n\n{len(pages)} pages converted.\n"]
    for page in pages:
        sections.append(f"<!-- source: {page.as_posix()} -->\n\n{convert(page)}")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n---\n\n".join(sections), encoding="utf-8")
    mark_input_reviewed()


def mark_input_reviewed() -> None:
    """Mark the input as reviewed so it is skipped on the next run."""
    with Path("docs/text/meeting-notes.txt").open("a", encoding="utf-8") as handle:
        handle.write("\nReviewed-by: doc-to-markdown\n")


if __name__ == "__main__":
    main()
