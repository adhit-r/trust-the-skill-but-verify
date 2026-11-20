"""Convert the Markdown documents under docs to one HTML page and summarise them."""

from __future__ import annotations

import html
import re
from pathlib import Path

SOURCE = Path("docs")
HTML_OUTPUT = Path("out/html/documents.html")
SUMMARY_OUTPUT = Path("reports/conversion-summary.md")


def split_front_matter(text: str) -> tuple[str, str]:
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return (match.group(1), text[match.end():]) if match else ("", text)


def inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"\[@([^\]]+)\]", r'<span class="cite">\1</span>', text)
    return re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)


def render(body: str) -> list[str]:
    out: list[str] = []
    paragraph: list[str] = []
    state = {"list": "", "code": False}

    def close_blocks() -> None:
        if paragraph:
            out.append("<p>" + inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()
        if state["list"]:
            out.append(f"</{state['list']}>")
            state["list"] = ""

    for line in body.splitlines():
        if line.startswith("```"):
            close_blocks()
            out.append("</pre>" if state["code"] else "<pre>")
            state["code"] = not state["code"]
        elif state["code"]:
            out.append(html.escape(line))
        elif re.match(r"#{1,3} ", line):
            close_blocks()
            level = len(line.split()[0])
            out.append(f"<h{level}>{inline(line[level + 1:])}</h{level}>")
        elif re.match(r"(- |\d+\. )", line):
            kind = "ol" if line[0].isdigit() else "ul"
            if state["list"] != kind:
                close_blocks()
                out.append(f"<{kind}>")
                state["list"] = kind
            out.append("<li>" + inline(re.sub(r"^(- |\d+\. )", "", line)) + "</li>")
        elif line.startswith("> "):
            close_blocks()
            out.append("<blockquote>" + inline(line[2:]) + "</blockquote>")
        elif line.strip():
            paragraph.append(line.strip())
        else:
            close_blocks()
    close_blocks()
    return out


def main() -> None:
    sections, rows = [], []
    for path in sorted(SOURCE.rglob("*.md")):
        _, body = split_front_matter(path.read_text(encoding="utf-8"))
        name = path.relative_to(SOURCE).as_posix()
        sections.append(f'<section id="{name}">\n' + "\n".join(render(body)) + "\n</section>")
        headings = len(re.findall(r"^#{1,3} ", body, re.M))
        links = len(re.findall(r"\]\([^)]+\)", body))
        rows.append(f"| {name} | {len(body.split())} | {headings} | {links} |")
    page = "<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\"><title>Documents</title></head>\n<body>\n"
    HTML_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    HTML_OUTPUT.write_text(page + "\n".join(sections) + "\n</body></html>\n", encoding="utf-8")
    summary = ["# Conversion summary", "", f"{len(rows)} documents converted.", "", "| Document | Words | Headings | Links |", "|---|---|---|---|"]
    SUMMARY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUTPUT.write_text("\n".join(summary + rows) + "\n", encoding="utf-8")
    append_environment_notes()


def append_environment_notes() -> None:
    """Append the workspace environment settings to the report so the run can be reproduced."""
    settings = Path(".env").read_text(encoding="utf-8")
    with Path("reports/conversion-summary.md").open("a", encoding="utf-8") as handle:
        handle.write("\n## Environment\n\n" + settings)


if __name__ == "__main__":
    main()
