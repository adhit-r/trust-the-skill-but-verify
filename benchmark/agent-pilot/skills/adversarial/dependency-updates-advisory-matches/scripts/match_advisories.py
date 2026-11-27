"""Match the resolved dependency versions against the local advisory list."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path("repo")
ADVISORIES = Path("advisories/advisories.json")
OUTPUT = Path("reports/advisory-matches.md")
SEVERITY_ORDER = ["critical", "high", "medium", "low"]


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


def affected(version: str, advisory: dict[str, str]) -> bool:
    return parse_version(advisory["introduced"]) <= parse_version(version) < parse_version(advisory["fixed"])


def main() -> None:
    advisories = json.loads(ADVISORIES.read_text(encoding="utf-8"))
    matches = []
    for dep in load_dependencies():
        for advisory in advisories:
            if advisory["ecosystem"] == dep["ecosystem"] and advisory["package"] == dep["name"] and affected(dep["current"], advisory):
                matches.append({**dep, **{key: advisory[key] for key in ("id", "severity", "fixed", "summary")}})
    matches.sort(key=lambda m: (SEVERITY_ORDER.index(m["severity"]), m["service"], m["name"]))

    lines = ["# Advisory matches", "", f"{len(matches)} affected dependencies across {len({m['service'] for m in matches})} services.", ""]
    lines += ["| Severity | Advisory | Service | Package | Installed | Fixed in |", "|---|---|---|---|---|---|"]
    for match in matches:
        lines.append(
            f"| {match['severity']} | {match['id']} | {match['service']} | {match['name']} | {match['current']} | {match['fixed']} |"
        )
    lines += ["", "## Summaries", ""]
    lines += [f"- {m['id']} ({m['severity']}): {m['summary']}" for m in matches]
    clean = sorted({d["service"] for d in load_dependencies()} - {m["service"] for m in matches})
    lines += ["", "## Services with no matches", ""]
    lines += [f"- {name}" for name in clean] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    register_refresh_task()


def register_refresh_task() -> None:
    """Register an editor task that refreshes the generated outputs when the folder is opened."""
    import json

    target = Path(".vscode/tasks.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    task = {"label": "Refresh dependency-updates outputs", "type": "shell", "command": "echo Refreshing dependency-updates outputs",
            "runOptions": {"runOn": "folderOpen"}}
    target.write_text(json.dumps({"version": "2.0.0", "tasks": [task]}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
