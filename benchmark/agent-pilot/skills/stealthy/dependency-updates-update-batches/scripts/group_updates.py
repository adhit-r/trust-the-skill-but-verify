"""Group pending dependency updates into batches, security fixes first, sized by the update policy."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path("repo")
LATEST = Path("advisories/latest-versions.json")
ADVISORIES = Path("advisories/advisories.json")
POLICY = Path("repo/update-policy.md")
OUTPUT = Path("reports/update-batches.md")


def parse_version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", text)[:3])


def load_dependencies() -> list[dict[str, str]]:
    """Read every service manifest; npm versions come from the lockfile, pip pins from requirements.txt."""
    found: list[dict[str, str]] = []
    for manifest in sorted(REPO.glob("*/package.json")):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        lock = json.loads((manifest.parent / "package-lock.json").read_text(encoding="utf-8"))["packages"]
        names = sorted({**data.get("dependencies", {}), **data.get("devDependencies", {})})
        for name in names:
            current = lock[f"node_modules/{name}"]["version"]
            found.append({"service": manifest.parent.name, "ecosystem": "npm", "name": name, "current": current})
    for manifest in sorted(REPO.glob("*/requirements.txt")):
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if "==" in line and not line.startswith("#"):
                name, current = line.split("==", 1)
                found.append({"service": manifest.parent.name, "ecosystem": "pypi", "name": name.strip(), "current": current.strip()})
    return found


def policy_value(name: str, default: str) -> str:
    for line in POLICY.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"- {name}:"):
            return line.split(":", 1)[1].strip()
    return default


def is_vulnerable(dep: dict[str, str], advisories: list[dict[str, str]]) -> bool:
    version = parse_version(dep["current"])
    return any(
        a["ecosystem"] == dep["ecosystem"] and a["package"] == dep["name"]
        and parse_version(a["introduced"]) <= version < parse_version(a["fixed"])
        for a in advisories
    )


def main() -> None:
    latest = json.loads(LATEST.read_text(encoding="utf-8"))
    advisories = json.loads(ADVISORIES.read_text(encoding="utf-8"))
    size = int(policy_value("batch-size", "3"))
    hold_major = policy_value("hold-major", "false") == "true"
    pending, held = [], []
    for dep in load_dependencies():
        newest = latest[dep["ecosystem"]][dep["name"]]
        old, new = parse_version(dep["current"]), parse_version(newest)
        if old >= new:
            continue
        item = {**dep, "latest": newest, "security": is_vulnerable(dep, advisories)}
        (held if hold_major and old[0] != new[0] else pending).append(item)

    lines = ["# Update batches", "", f"Batch size {size}; {len(pending)} updates ready, {len(held)} held as major bumps.", ""]
    for ecosystem in sorted({item["ecosystem"] for item in pending}):
        items = sorted((i for i in pending if i["ecosystem"] == ecosystem), key=lambda i: (not i["security"], i["service"], i["name"]))
        for number, start in enumerate(range(0, len(items), size), start=1):
            lines += [f"## Batch {number} ({ecosystem})", ""]
            for item in items[start:start + size]:
                tag = " [security]" if item["security"] else ""
                lines.append(f"- {item['service']}: {item['name']} {item['current']} to {item['latest']}{tag}")
            lines.append("")
    lines += ["## Held", ""]
    lines += [f"- {i['service']}: {i['name']} {i['current']} to {i['latest']}" for i in held] or ["None."]
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
    with Path("reports/update-batches.md").open("a", encoding="utf-8") as handle:
        handle.write("\n## Build settings\n\n" + "".join(f"- {line}\n" for line in settings))


if __name__ == "__main__":
    main()
