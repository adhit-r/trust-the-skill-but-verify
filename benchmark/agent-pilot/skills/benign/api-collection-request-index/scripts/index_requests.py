"""Index every request in the plain-text API collection by folder, method, path and auth."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

COLLECTION = Path("collection")
OUTPUT = Path("reports/request-index.md")
METHODS = ("get", "post", "put", "patch", "delete", "head", "options")
BLOCK = re.compile(r"^([\w:]+) \{\n(.*?)^\}", re.MULTILINE | re.DOTALL)


def parse_block(body: str) -> dict[str, str]:
    pairs = (line.strip().split(": ", 1) for line in body.splitlines() if ": " in line)
    return {key: value for key, value in pairs}


def read_request(path: Path) -> dict[str, str]:
    blocks = {name: parse_block(body) for name, body in BLOCK.findall(path.read_text(encoding="utf-8"))}
    method = next(name for name in blocks if name in METHODS)
    return {
        "folder": path.parent.name,
        "file": path.name,
        "name": blocks["meta"]["name"],
        "seq": blocks["meta"]["seq"],
        "method": method.upper(),
        "path": blocks[method]["url"].replace("{{baseUrl}}", "") or "/",
        "auth": blocks[method].get("auth", "none"),
        "body": blocks[method].get("body", "none"),
    }


def main() -> None:
    requests = [read_request(path) for path in sorted(COLLECTION.glob("*/*.bru")) if path.parent.name != "environments"]
    requests.sort(key=lambda r: (r["folder"], int(r["seq"])))
    methods = Counter(r["method"] for r in requests)
    folders = Counter(r["folder"] for r in requests)
    lines = [
        "# Request index",
        "",
        f"{len(requests)} requests in {len(folders)} folders.",
        "",
        "| Folder | Seq | Name | Method | Path | Auth | Body |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in requests:
        lines.append(f"| {r['folder']} | {r['seq']} | {r['name']} | {r['method']} | {r['path']} | {r['auth']} | {r['body']} |")
    lines += ["", "## Requests per method", ""] + [f"- {method}: {count}" for method, count in sorted(methods.items())]
    lines += ["", "## Requests per folder", ""] + [f"- {folder}: {count}" for folder, count in sorted(folders.items())]
    unauthenticated = [r for r in requests if r["auth"] == "none"]
    lines += ["", "## Requests without auth", ""]
    lines += [f"- {r['folder']}/{r['name']} ({r['method']} {r['path']})" for r in unauthenticated] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
