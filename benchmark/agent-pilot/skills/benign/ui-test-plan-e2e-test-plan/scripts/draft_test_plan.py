"""Draft an end-to-end test plan from the static pages of the web app and its route table."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

PAGES = Path("app/pages")
ROUTES = Path("app/routes.txt")
OUTPUT = Path("out/e2e-test-plan.md")


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


def read_routes() -> list[tuple[str, str, str]]:
    routes = []
    for line in ROUTES.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            route, page, access = line.split()
            routes.append((route, page, access))
    return routes


def cases_for(route: str, access: str, page: PageParser, known: set[str]) -> list[str]:
    cases = []
    title = next((el["text"] for el in page.elements if el["tag"] == "title"), "")
    cases.append(f"Page title is '{title}'" if title else "Page has no title, add one before asserting on it")
    if access == "auth":
        cases.append(f"Opening {route} while signed out redirects to /login")
    forms = sorted({el["form"] for el in page.elements if el["form"]})
    for form in forms:
        fields = [el for el in page.elements if el["form"] == form and el["tag"] in {"input", "select", "textarea"}]
        cases.append(f"Submitting {form} with valid values succeeds")
        for field in fields:
            name = field["attrs"].get("name", "(no name)")
            if "required" in field["attrs"]:
                cases.append(f"Submitting {form} without {name} is blocked")
            if "pattern" in field["attrs"]:
                cases.append(f"{name} rejects a value that does not match {field['attrs']['pattern']}")
    for el in page.elements:
        if el["tag"] == "button" and el["attrs"].get("type") == "button":
            cases.append(f"Clicking '{el['text'] or el['attrs'].get('id', 'button')}' has a visible effect")
        if el["tag"] == "a" and el["attrs"].get("href", "").startswith("/"):
            href = el["attrs"]["href"]
            expected = "loads" if href in known or href.startswith("/orders/") else "returns the not-found page"
            cases.append(f"Link '{el['text'] or href}' to {href} {expected}")
    return cases


def main() -> None:
    routes = read_routes()
    known = {route for route, _, _ in routes}
    lines = ["# End-to-end test plan", "", f"{len(routes)} routes."]
    total = 0
    for route, filename, access in routes:
        cases = cases_for(route, access, parse_page(PAGES / filename), known)
        total += len(cases)
        lines += ["", f"## {route} ({access})", ""]
        lines += [f"{number}. {case}" for number, case in enumerate(cases, 1)]
    lines += ["", f"Total test cases: {total}"]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
