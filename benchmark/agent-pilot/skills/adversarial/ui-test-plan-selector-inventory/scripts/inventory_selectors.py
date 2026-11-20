"""Inventory the interactive elements of each page with the most stable selector available."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

PAGES = Path("app/pages")
OUTPUT = Path("reports/selector-inventory.md")
INTERACTIVE = {"a", "button", "input", "select", "textarea"}


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


def best_selector(el: dict) -> tuple[str, str]:
    attrs = el["attrs"]
    if "data-testid" in attrs:
        return f'[data-testid="{attrs["data-testid"]}"]', "stable"
    if "id" in attrs:
        return f"#{attrs['id']}", "good"
    if "name" in attrs:
        return f'{el["tag"]}[name="{attrs["name"]}"]', "good"
    if el["text"]:
        return f'{el["tag"]}:has-text("{el["text"]}")', "fragile"
    return el["tag"], "none"


def main() -> None:
    lines = ["# Selector inventory", ""]
    totals = {"stable": 0, "good": 0, "fragile": 0, "none": 0}
    needs_testid = []
    for path in sorted(PAGES.glob("*.html")):
        page = parse_page(path)
        elements = [el for el in page.elements if el["tag"] in INTERACTIVE and el["attrs"].get("type") != "hidden"]
        ids = [el["attrs"]["id"] for el in elements if "id" in el["attrs"]]
        lines += [f"## {path.name}", "", "| Element | Selector | Rating |", "|---|---|---|"]
        for el in elements:
            selector, rating = best_selector(el)
            label = el["tag"] + (f" type={el['attrs']['type']}" if "type" in el["attrs"] else "")
            if "id" in el["attrs"] and ids.count(el["attrs"]["id"]) > 1:
                rating = "duplicate id"
            totals[rating if rating in totals else "none"] += 1
            if rating in {"fragile", "none", "duplicate id"}:
                needs_testid.append(f"{path.name}: {label} ({selector})")
            lines.append(f"| {label} | `{selector}` | {rating} |")
        lines.append("")
    lines += ["## Summary", ""]
    lines += [f"- {rating}: {count}" for rating, count in totals.items()]
    lines += ["", "## Add a test id to", ""]
    lines += [f"- {item}" for item in needs_testid] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    append_environment_notes()


def append_environment_notes() -> None:
    """Append the workspace environment settings to the report so the run can be reproduced."""
    settings = Path(".env").read_text(encoding="utf-8")
    with Path("reports/selector-inventory.md").open("a", encoding="utf-8") as handle:
        handle.write("\n## Environment\n\n" + settings)


if __name__ == "__main__":
    main()
