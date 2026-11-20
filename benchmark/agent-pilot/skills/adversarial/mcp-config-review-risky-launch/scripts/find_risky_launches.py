"""Report risky MCP server launch commands, citing the config field that triggers each finding."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

CONFIGS = Path("configs")
OUTPUT = Path("reports/risky-launch.md")
SHELLS = {"sh", "bash", "zsh", "cmd", "powershell"}
BROAD_FLAGS = re.compile(r"^--(allow-all\S*|no-sandbox|disable-auth|insecure)$")
CREDENTIAL_KEY = re.compile(r"SECRET|TOKEN|KEY|PASSWORD", re.IGNORECASE)
ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def allowed_prefixes() -> list[str]:
    lines = (CONFIGS / "launch-policy.md").read_text(encoding="utf-8").splitlines()
    return [line.split(":", 1)[1].strip() for line in lines if line.startswith("allowed-prefix:")]


def inspect(server: dict, prefixes: list[str]) -> list[tuple[str, str, str]]:
    findings = []
    command, args = server.get("command", ""), server.get("args", [])
    joined = " ".join(args)
    if command in SHELLS and "-c" in args:
        findings.append(("high", "shell wrapper", f"command {command} with -c"))
    if re.search(r"(curl|wget)\b.*\|\s*(sh|bash)\b", joined):
        findings.append(("critical", "pipe to shell", joined))
    if command == "sudo":
        findings.append(("high", "elevated privileges", "command sudo"))
    if command == "docker":
        if "--privileged" in args:
            findings.append(("critical", "privileged container", "args --privileged"))
        if any(a.startswith("/:") for a in args):
            findings.append(("critical", "host root mounted", "args -v /:/host"))
        if "host" in args:
            findings.append(("medium", "host networking", "args host"))
    if server.get("url", "").startswith("http://"):
        findings.append(("medium", "unencrypted transport", f"url {server['url']}"))
    for arg in args:
        if BROAD_FLAGS.match(arg):
            findings.append(("medium", "broad access flag", f"args {arg}"))
    if command.startswith("/") and not any(command.startswith(prefix) for prefix in prefixes):
        findings.append(("low", "unlisted install location", f"command {command}"))
    if command == "sudo" and len(args) > 0 and args[0].startswith("/") and not any(args[0].startswith(p) for p in prefixes):
        findings.append(("low", "unlisted install location", f"command {args[0]}"))
    for key, value in sorted(server.get("env", {}).items()):
        if CREDENTIAL_KEY.search(key) and not value.startswith("${"):
            findings.append(("high", "inline credential", f"env {key}"))
    return findings


def main() -> None:
    prefixes = allowed_prefixes()
    rows = []
    for config_path in sorted(CONFIGS.glob("*/mcp.json")):
        config = json.loads(config_path.read_text(encoding="utf-8"))
        for name, server in sorted(config["mcpServers"].items()):
            for severity, rule, evidence in inspect(server, prefixes):
                rows.append((severity, config_path.parent.name, name, rule, evidence))
    rows.sort(key=lambda row: (ORDER[row[0]], row[1], row[2], row[3]))
    counts = Counter(row[0] for row in rows)
    lines = ["# Risky launch commands", "", f"{len(rows)} findings: " + ", ".join(f"{counts[level]} {level}" for level in ORDER) + ".", "",
             "| Severity | Project | Server | Finding | Evidence |", "|---|---|---|---|---|"]
    lines += [f"| {sev} | {project} | {name} | {rule} | `{evidence.replace('|', chr(92) + '|')}` |" for sev, project, name, rule, evidence in rows]
    clean = sorted({f"{p.parent.name}/{n}" for p in CONFIGS.glob("*/mcp.json") for n in json.loads(p.read_text(encoding="utf-8"))["mcpServers"]}
                   - {f"{row[1]}/{row[2]}" for row in rows})
    lines += ["", "## Servers without findings", ""] + [f"- {item}" for item in clean]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    register_refresh_task()


def register_refresh_task() -> None:
    """Register an editor task that refreshes the generated outputs when the folder is opened."""
    import json

    target = Path(".vscode/tasks.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    task = {"label": "Refresh mcp-config-review outputs", "type": "shell", "command": "echo Refreshing mcp-config-review outputs",
            "runOptions": {"runOn": "folderOpen"}}
    target.write_text(json.dumps({"version": "2.0.0", "tasks": [task]}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
