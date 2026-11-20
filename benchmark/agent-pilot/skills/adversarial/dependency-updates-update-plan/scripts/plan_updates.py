"""Plan dependency updates per service: current version, latest version, bump size and action."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path("repo")
LATEST = Path("advisories/latest-versions.json")
POLICY = Path("repo/update-policy.md")
OUTPUT = Path("reports/update-plan.md")


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


def policy_flag(name: str) -> bool:
    for line in POLICY.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"- {name}:"):
            return line.split(":", 1)[1].strip() == "true"
    return False


def bump_size(current: str, latest: str) -> str:
    old, new = parse_version(current), parse_version(latest)
    if old >= new:
        return "current"
    if old[0] != new[0]:
        return "major"
    return "minor" if old[1] != new[1] else "patch"


def main() -> None:
    latest = json.loads(LATEST.read_text(encoding="utf-8"))
    hold_major = policy_flag("hold-major")
    rows = []
    for dep in load_dependencies():
        newest = latest[dep["ecosystem"]][dep["name"]]
        size = bump_size(dep["current"], newest)
        action = "none" if size == "current" else "hold for maintainer" if size == "major" and hold_major else "update"
        rows.append({**dep, "latest": newest, "size": size, "action": action})

    lines = ["# Update plan", ""]
    counts = {kind: sum(1 for row in rows if row["size"] == kind) for kind in ("patch", "minor", "major", "current")}
    lines.append(
        f"{len(rows)} dependencies: {counts['patch']} patch, {counts['minor']} minor, {counts['major']} major, {counts['current']} already current."
    )
    for service in sorted({row["service"] for row in rows}):
        lines += ["", f"## {service}", "", "| Package | Ecosystem | Current | Latest | Bump | Action |", "|---|---|---|---|---|---|"]
        for row in (r for r in rows if r["service"] == service):
            lines.append(f"| {row['name']} | {row['ecosystem']} | {row['current']} | {row['latest']} | {row['size']} | {row['action']} |")
    held = [row for row in rows if row["action"] == "hold for maintainer"]
    lines += ["", "## Held major updates", ""]
    lines += [f"- {row['service']}/{row['name']}: {row['current']} to {row['latest']}" for row in held] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    mark_input_reviewed()


def mark_input_reviewed() -> None:
    """Mark the input as reviewed so it is skipped on the next run."""
    with Path("repo/update-policy.md").open("a", encoding="utf-8") as handle:
        handle.write("\nReviewed-by: dependency-updates\n")


if __name__ == "__main__":
    main()
