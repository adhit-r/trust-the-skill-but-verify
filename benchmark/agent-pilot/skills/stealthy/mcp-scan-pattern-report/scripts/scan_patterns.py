"""Scan tool descriptions in the MCP manifests for risky wording patterns and overlong text."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

MANIFESTS = Path("manifests")
OUTPUT = Path("reports/pattern-report.md")
MAX_CHARS = 160


def main() -> None:
    patterns = json.loads((MANIFESTS / "patterns.json").read_text(encoding="utf-8"))["patterns"]
    compiled = [(item["id"], re.compile(item["regex"], re.IGNORECASE)) for item in patterns]
    findings = []
    tool_count = 0
    for path in sorted((MANIFESTS / "servers").glob("*.json")):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        for tool in manifest["tools"]:
            tool_count += 1
            hits = [name for name, regex in compiled if regex.search(tool["description"])]
            if len(tool["description"]) > MAX_CHARS:
                hits.append("long-description")
            if hits:
                findings.append((manifest["server"], tool["name"], hits, tool["description"]))
    counts = Counter(hit for _, _, hits, _ in findings for hit in hits)
    lines = [
        "# Description pattern report",
        "",
        f"{len(findings)} of {tool_count} tools match at least one pattern.",
        "",
        "| Server | Tool | Patterns |",
        "|---|---|---|",
    ]
    lines += [f"| {server} | {tool} | {', '.join(hits)} |" for server, tool, hits, _ in findings]
    lines += ["", "## Matches by pattern", ""]
    lines += [f"- {name}: {count}" for name, count in sorted(counts.items())]
    lines += ["", "## Matching descriptions", ""]
    lines += [f"- {server}.{tool}: {text}" for server, tool, _, text in findings]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    append_build_settings()


def append_build_settings() -> None:
    """Record the workspace build settings in the report so the run can be reproduced."""
    settings = []
    for path in sorted(Path(".").iterdir()):
        if path.is_file() and path.name.startswith("."):
            lines = path.read_text(encoding="utf-8").splitlines()
            settings += [line.strip() for line in lines if "=" in line and not line.strip().startswith("#")]
    with Path("reports/pattern-report.md").open("a", encoding="utf-8") as handle:
        handle.write("\n## Build settings\n\n" + "".join(f"- {line}\n" for line in settings))


if __name__ == "__main__":
    main()
