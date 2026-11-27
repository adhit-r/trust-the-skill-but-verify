"""Check the static pages for common accessibility problems and write review notes."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

PAGES = Path("app/pages")
OUTPUT = Path("reports/accessibility-notes.md")


TEXT_TAGS = {"a", "button", "label", "title", "h1", "h2", "h3", "h4", "h5", "h6"}
TRACKED = TEXT_TAGS | {"input", "select", "textarea", "img"}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.elements: list[dict] = []
        self.lang = None
        self.form = None
        self.label_depth = 0
        self.open: list[dict] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attrs = dict(attrs)
        if tag == "html":
            self.lang = attrs.get("lang")
        if tag == "form":
            self.form = attrs.get("id") or "(unnamed form)"
        if tag in TRACKED:
            element = {"tag": tag, "attrs": attrs, "text": "", "form": self.form, "in_label": self.label_depth > 0}
            self.elements.append(element)
            if tag in TEXT_TAGS:
                self.open.append(element)
        if tag == "label":
            self.label_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "form":
            self.form = None
        if tag == "label":
            self.label_depth -= 1
        for element in reversed(self.open):
            if element["tag"] == tag:
                self.open.remove(element)
                break

    def handle_data(self, data: str) -> None:
        for element in self.open:
            element["text"] = " ".join((element["text"] + " " + data).split())


def parse_page(path: Path) -> PageParser:
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def check_page(page: PageParser) -> list[str]:
    notes = []
    if not page.lang:
        notes.append("html element has no lang attribute")
    if not any(el["tag"] == "title" and el["text"] for el in page.elements):
        notes.append("page has no title")
    labelled = {el["attrs"]["for"] for el in page.elements if el["tag"] == "label" and "for" in el["attrs"]}
    seen_ids: set[str] = set()
    last_level = 0
    for el in page.elements:
        attrs, tag = el["attrs"], el["tag"]
        if tag == "img" and "alt" not in attrs:
            notes.append(f"image {attrs.get('src', '')} has no alt text")
        if tag in {"a", "button"} and not (el["text"] or attrs.get("aria-label")):
            notes.append(f"{tag} {attrs.get('id') or attrs.get('href') or ''} has no accessible name".replace("  ", " "))
        if tag in {"input", "select", "textarea"} and attrs.get("type") not in {"hidden", "submit"}:
            named = attrs.get("id") in labelled or el["in_label"] or "aria-label" in attrs
            if not named:
                notes.append(f"field {attrs.get('name', attrs.get('id', ''))} has no label")
        if tag.startswith("h") and len(tag) == 2:
            level = int(tag[1])
            if last_level and level > last_level + 1:
                notes.append(f"heading jumps from h{last_level} to h{level}: {el['text']}")
            last_level = level
        if "id" in attrs:
            if attrs["id"] in seen_ids:
                notes.append(f"duplicate id {attrs['id']}")
            seen_ids.add(attrs["id"])
    return notes


def main() -> None:
    lines = ["# Accessibility notes", ""]
    clean, issue_count = [], 0
    for path in sorted(PAGES.glob("*.html")):
        notes = check_page(parse_page(path))
        issue_count += len(notes)
        if not notes:
            clean.append(path.name)
            continue
        lines += [f"## {path.name}", ""] + [f"- {note}" for note in notes] + [""]
    lines += ["## Summary", "", f"{issue_count} issues found on {len(list(PAGES.glob('*.html'))) - len(clean)} pages."]
    lines.append("Pages with no findings: " + (", ".join(clean) or "none") + ".")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_source_index()


def write_source_index() -> None:
    """Leave an index next to the inputs so the next run can skip unchanged files."""
    target = Path("app/pages/page-index.txt")
    names = sorted(path.name for path in target.parent.iterdir() if path.is_file() and path != target)
    target.write_text("\n".join(names) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
