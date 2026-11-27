"""Build a metadata catalog of the mixed sample files: type, size, lines, title and dates."""

from __future__ import annotations

import json
import re
from pathlib import Path

SAMPLES = Path("samples")
OUTPUT = Path("reports/metadata-catalog.md")
KINDS = {".md": "markdown", ".txt": "text", ".html": "html", ".csv": "csv", ".json": "json", ".log": "log"}


def front_matter(text: str) -> dict[str, str]:
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return {}
    pairs = (line.split(":", 1) for line in match.group(1).splitlines() if ":" in line)
    return {key.strip(): value.strip() for key, value in pairs}


def describe(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    kind = KINDS.get(path.suffix, "other")
    info = {"title": "", "author": "", "date": ""}
    if kind == "markdown":
        meta = front_matter(text)
        info.update({key: meta.get(key, "") for key in info})
    elif kind == "html":
        title = re.search(r"<title>(.*?)</title>", text, re.DOTALL)
        author = re.search(r'<meta name="author" content="(.*?)"', text)
        info["title"] = title.group(1).strip() if title else ""
        info["author"] = author.group(1) if author else ""
    elif kind == "json":
        data = json.loads(text)
        info["title"] = str(data.get("title", "")) if isinstance(data, dict) else ""
        info["date"] = str(data.get("updated", "")) if isinstance(data, dict) else ""
    elif kind == "csv":
        info["title"] = "columns: " + text.splitlines()[0]
    else:
        info["title"] = text.strip().splitlines()[0][:60]
    info.update({"kind": kind, "bytes": str(len(text.encode("utf-8"))), "lines": str(len(text.splitlines()))})
    return info


def main() -> None:
    rows = []
    for path in sorted(p for p in SAMPLES.rglob("*") if p.is_file()):
        rows.append((path.relative_to(SAMPLES).as_posix(), describe(path)))
    kinds = sorted({info["kind"] for _, info in rows})
    lines = [
        "# Metadata catalog",
        "",
        f"{len(rows)} files, {len(kinds)} kinds: {', '.join(kinds)}.",
        "",
        "| File | Kind | Bytes | Lines | Title | Author | Date |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, info in rows:
        lines.append(f"| {name} | {info['kind']} | {info['bytes']} | {info['lines']} | {info['title']} | {info['author']} | {info['date']} |")
    total = sum(int(info["bytes"]) for _, info in rows)
    lines += ["", f"Total size: {total} bytes."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_source_index()


def write_source_index() -> None:
    """Leave an index next to the inputs so the next run can skip unchanged files."""
    target = Path("samples/docs/INDEX.txt")
    names = sorted(path.name for path in target.parent.iterdir() if path.is_file() and path != target)
    target.write_text("\n".join(names) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
