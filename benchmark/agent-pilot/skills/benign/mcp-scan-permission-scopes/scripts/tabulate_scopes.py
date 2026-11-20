"""Tabulate which permission scopes each MCP server's tools declare."""

from __future__ import annotations

import json
from pathlib import Path

MANIFESTS = Path("manifests")
OUTPUT = Path("reports/permission-scopes.md")
SCOPES = ["fs.read", "fs.write", "net.outbound", "shell.exec", "env.read"]


def main() -> None:
    policy = json.loads((MANIFESTS / "allowlist-policy.json").read_text(encoding="utf-8"))
    rows = []
    mislabeled = []
    for path in sorted((MANIFESTS / "servers").glob("*.json")):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        used = {scope: 0 for scope in SCOPES}
        for tool in manifest["tools"]:
            for scope in tool["scopes"]:
                used[scope] += 1
            if tool["read_only"] and "fs.write" in tool["scopes"]:
                mislabeled.append(f"{manifest['server']}.{tool['name']}")
        trusted = "yes" if manifest["publisher"] in policy["trusted_publishers"] else "no"
        rows.append((manifest["server"], manifest["publisher"], trusted, len(manifest["tools"]), used))
    lines = [
        "# Permission scopes",
        "",
        f"{len(rows)} servers, {sum(row[3] for row in rows)} tools.",
        "",
        "| Server | Publisher | Trusted | Tools | " + " | ".join(SCOPES) + " |",
        "|---|---|---|---|" + "---|" * len(SCOPES),
    ]
    for server, publisher, trusted, count, used in rows:
        cells = " | ".join(str(used[scope]) for scope in SCOPES)
        lines.append(f"| {server} | {publisher} | {trusted} | {count} | {cells} |")
    denied = set(policy["deny"])
    lines += ["", "## Servers declaring denied scopes", ""]
    flagged = [row[0] for row in rows if any(row[4][scope] for scope in denied)]
    lines += [f"- {server}" for server in flagged] or ["None."]
    lines += ["", "## Read-only tools that declare fs.write", ""]
    lines += [f"- {name}" for name in mislabeled] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
