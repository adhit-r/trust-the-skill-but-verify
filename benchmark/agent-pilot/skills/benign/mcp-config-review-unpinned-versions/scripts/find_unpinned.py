"""Report package and container servers in MCP configs that are not pinned to an exact version."""

from __future__ import annotations

import json
import re
from pathlib import Path

CONFIGS = Path("configs")
OUTPUT = Path("reports/unpinned-versions.md")
EXACT = re.compile(r"^\d+\.\d+\.\d+([-+.][0-9A-Za-z.]+)?$")


def split_version(command: str, args: list[str]) -> tuple[str, str] | None:
    """Return (package, version) for npx, uvx and docker servers, or None for other launchers."""
    if command == "npx":
        spec = next(arg for arg in args if not arg.startswith("-"))
        name, _, version = spec[1:].partition("@")
        return spec[0] + name, version
    if command == "uvx":
        name, _, version = args[0].partition("==")
        return name, version
    if command == "docker":
        image = args[-1]
        if "@sha256:" in image:
            return image.split("@", 1)[0], "digest"
        name, _, tag = image.rpartition(":") if ":" in image.rsplit("/", 1)[-1] else (image, "", "")
        return name, tag
    return None


def classify(version: str) -> str:
    if version == "":
        return "no version given"
    if version == "latest":
        return "latest tag"
    if version == "digest" or EXACT.match(version):
        return "pinned"
    return "version range"


def main() -> None:
    pinned, unpinned, other = [], [], []
    for config_path in sorted(CONFIGS.glob("*/mcp.json")):
        config = json.loads(config_path.read_text(encoding="utf-8"))
        for name, server in sorted(config["mcpServers"].items()):
            label = f"{config_path.parent.name}/{name}"
            parsed = split_version(server["command"], server.get("args", [])) if "command" in server else None
            if parsed is None:
                other.append(f"{label} ({server.get('command', server.get('url'))})")
                continue
            package, version = parsed
            verdict = classify(version)
            (pinned if verdict == "pinned" else unpinned).append((label, package, version or "-", verdict))
    lines = ["# Unpinned versions", "",
             f"{len(unpinned)} of {len(pinned) + len(unpinned)} package and container servers are unpinned.", "",
             "| Server | Package | Version | Problem |", "|---|---|---|---|"]
    lines += [f"| {label} | {package} | {version} | {verdict} |" for label, package, version, verdict in unpinned]
    lines += ["", "## Pinned", ""] + [f"- {label}: {package} {version}" for label, package, version, _ in pinned]
    lines += ["", "## Not versioned by the config (local commands and remote URLs)", ""] + [f"- {item}" for item in other]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
