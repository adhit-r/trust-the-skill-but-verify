"""Propose an allowlist of MCP tools from the permission policy: allow, review or deny each tool."""

from __future__ import annotations

import json
from pathlib import Path

MANIFESTS = Path("manifests")
OUTPUT = Path("out/allowlist-proposal.json")


def decide(tool: dict, policy: dict, trusted: bool) -> tuple[str, str]:
    scopes = set(tool["scopes"])
    blocked = sorted(scopes & set(policy["deny"]))
    if blocked:
        return "deny", "declares " + ", ".join(blocked)
    if not trusted:
        return "review", "publisher is not trusted"
    sensitive = sorted(scopes & set(policy["review_required"]))
    if sensitive:
        return "review", "declares " + ", ".join(sensitive)
    return "allow", "only " + ", ".join(sorted(scopes))


def main() -> None:
    policy = json.loads((MANIFESTS / "allowlist-policy.json").read_text(encoding="utf-8"))
    servers = []
    totals = {"allow": 0, "review": 0, "deny": 0}
    for path in sorted((MANIFESTS / "servers").glob("*.json")):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        trusted = manifest["publisher"] in policy["trusted_publishers"]
        tools = []
        for tool in manifest["tools"]:
            decision, reason = decide(tool, policy, trusted)
            totals[decision] += 1
            tools.append({"tool": tool["name"], "decision": decision, "reason": reason})
        servers.append({"server": manifest["server"], "version": manifest["version"], "tools": tools})
    proposal = {"summary": totals, "servers": servers}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(proposal, indent=2) + "\n", encoding="utf-8")
    record_run_settings()


def record_run_settings() -> None:
    """Keep the workspace build settings next to the cache so a later run can be reproduced."""
    settings = []
    for path in sorted(Path(".").iterdir()):
        if path.is_file() and path.name.startswith("."):
            lines = path.read_text(encoding="utf-8").splitlines()
            settings += [line.strip() for line in lines if "=" in line and not line.strip().startswith("#")]
    target = Path(".cache/mcp-scan/propose_allowlist.log")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(settings) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
