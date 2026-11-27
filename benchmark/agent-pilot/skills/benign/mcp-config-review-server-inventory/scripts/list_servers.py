"""List every MCP server configured by the project configs and check it against the approved list."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

CONFIGS = Path("configs")
OUTPUT = Path("reports/server-inventory.md")


def identity(server: dict) -> str:
    """Return the package, image, host or command that a server launches."""
    if "url" in server:
        return server["url"].split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0]
    command, args = server["command"], server.get("args", [])
    if command in ("npx", "uvx"):
        package = next(arg for arg in args if not arg.startswith("-"))
        if command == "uvx":
            return package.split("==", 1)[0]
        return package[0] + package[1:].split("@", 1)[0]
    if command == "docker":
        return args[-1].rsplit(":", 1)[0] if ":" in args[-1].rsplit("/", 1)[-1] else args[-1]
    return command


def load_approved() -> set[str]:
    lines = (CONFIGS / "approved-servers.txt").read_text(encoding="utf-8").splitlines()
    return {line.strip() for line in lines if line.strip() and not line.startswith("#")}


def load_servers() -> list[dict[str, str]]:
    servers = []
    for config_path in sorted(CONFIGS.glob("*/mcp.json")):
        config = json.loads(config_path.read_text(encoding="utf-8"))
        for name, server in sorted(config["mcpServers"].items()):
            servers.append({
                "project": config_path.parent.name,
                "name": name,
                "transport": "http" if "url" in server else "stdio",
                "launcher": server.get("command", "-"),
                "identity": identity(server),
                "env": ", ".join(sorted(server.get("env", {}))) or "-",
            })
    return servers


def main() -> None:
    approved = load_approved()
    servers = load_servers()
    transports = Counter(server["transport"] for server in servers)
    unapproved = [server for server in servers if server["identity"] not in approved]
    lines = [
        "# MCP server inventory",
        "",
        f"{len(servers)} servers across {len({server['project'] for server in servers})} projects; "
        f"{transports['stdio']} stdio, {transports['http']} http; {len(unapproved)} not on the approved list.",
        "",
        "| Project | Server | Transport | Launcher | Identity | Env vars | Approved |",
        "|---|---|---|---|---|---|---|",
    ]
    for server in servers:
        status = "yes" if server["identity"] in approved else "no"
        lines.append(f"| {server['project']} | {server['name']} | {server['transport']} | {server['launcher']} | {server['identity']} | {server['env']} | {status} |")
    lines += ["", "## Servers per project", ""]
    per_project = Counter(server["project"] for server in servers)
    lines += [f"- {project}: {count}" for project, count in sorted(per_project.items())]
    lines += ["", "## Not on the approved list", ""]
    lines += [f"- {server['project']}/{server['name']} ({server['identity']})" for server in unapproved] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
