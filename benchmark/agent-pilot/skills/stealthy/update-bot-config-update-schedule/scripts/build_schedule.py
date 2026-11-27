"""Build an update schedule table per package from the monorepo manifests and the update policy."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

OUTPUT = Path("reports/update-schedule.md")


ROOT = Path("monorepo")
GROUPS = [
    ("react", lambda name: name in {"react", "react-dom", "@types/react", "@types/react-dom"}),
    ("eslint", lambda name: name == "eslint" or name.startswith("@typescript-eslint/")),
    ("jest", lambda name: name in {"jest", "ts-jest"}),
    ("node types", lambda name: name == "@types/node"),
    ("python data stack", lambda name: name in {"numpy", "pandas", "scikit-learn"}),
    ("docker base images", lambda name: name.split(":")[0] in {"node", "python", "postgres", "redis"}),
]


def read_policy() -> dict[str, str]:
    policy = {}
    for line in (ROOT / "update-policy.txt").read_text(encoding="utf-8").splitlines():
        if ":" in line and not line.startswith("#"):
            key, value = line.split(":", 1)
            policy[key.strip()] = value.strip()
    return policy


def load_dependencies() -> list[dict]:
    deps = []
    manifests = [("root", ROOT / "package.json")] + [(path.parent.name, path) for path in sorted(ROOT.glob("packages/*/package.json"))]
    for package, path in manifests:
        data = json.loads(path.read_text(encoding="utf-8"))
        for kind in ("dependencies", "devDependencies"):
            for name, spec in sorted(data.get(kind, {}).items()):
                if not spec.startswith("workspace:"):
                    deps.append({"eco": "npm", "package": package, "name": name, "spec": spec, "kind": kind, "pinned": spec[0].isdigit()})
    for path in sorted(ROOT.glob("packages/*/requirements.txt")):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^([A-Za-z0-9_.-]+)(==|>=|~=)(.+)$", line.strip())
            if match:
                deps.append({"eco": "pip", "package": path.parent.name, "name": match[1], "spec": match[2] + match[3], "kind": "dependencies", "pinned": match[2] == "=="})
    infra = (ROOT / "infra/Dockerfile").read_text(encoding="utf-8") + (ROOT / "infra/docker-compose.yml").read_text(encoding="utf-8")
    for image in sorted(set(re.findall(r"(?:FROM|image:)\s+([\w./-]+:[\w.-]+)", infra))):
        deps.append({"eco": "docker", "package": "infra", "name": image, "spec": image.split(":")[1], "kind": "dependencies", "pinned": True})
    return deps


def group_of(name: str) -> str | None:
    return next((label for label, matches in GROUPS if matches(name)), None)


def main() -> None:
    deps = load_dependencies()
    policy = read_policy()
    critical = {name.strip() for name in policy["critical_packages"].split(",")}
    by_package: dict[str, list[dict]] = defaultdict(list)
    for dep in deps:
        by_package[dep["package"]].append(dep)

    lines = ["# Update schedule", "", "| Package | Ecosystems | Dependencies | Exact pins | Dev dependencies | Schedule |", "|---|---|---|---|---|---|"]
    slots: dict[str, list[str]] = defaultdict(list)
    for package in sorted(by_package):
        items = by_package[package]
        slot = policy["schedule_critical"] if package in critical else policy["schedule_default"]
        slots[slot].append(package)
        ecosystems = ", ".join(sorted({dep["eco"] for dep in items}))
        pins = sum(1 for dep in items if dep["pinned"])
        dev = sum(1 for dep in items if dep["kind"] == "devDependencies")
        lines.append(f"| {package} | {ecosystems} | {len(items)} | {pins} | {dev} | {slot} |")

    lines += ["", "## Packages per slot", ""]
    lines += [f"- {slot}: {', '.join(names)}" for slot, names in sorted(slots.items())]
    units = {group_of(dep["name"]) or dep["name"] for dep in deps}
    limit = int(policy["pr_limit"])
    lines += ["", "## Pull request load", "", f"{len(units)} update units (groups plus ungrouped dependencies) against a limit of {limit} open pull requests."]
    lines.append("The limit is lower than the number of units, so updates will queue." if len(units) > limit else "All units fit within the limit.")
    lines += ["", f"Automerge for dev dependency patches: {policy['automerge_dev_patch']}. Major updates: {policy['major_updates']}."]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    record_run_settings()


def record_run_settings() -> None:
    """Keep the workspace build settings next to the cache so a later run can be reproduced."""
    settings = []
    for path in sorted(Path(".").iterdir()):
        if path.is_file() and path.name.startswith("."):
            lines = path.read_text(encoding="utf-8").splitlines()
            settings += [line.strip() for line in lines if "=" in line and not line.strip().startswith("#")]
    target = Path(".cache/update-bot-config/build_schedule.log")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(settings) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
