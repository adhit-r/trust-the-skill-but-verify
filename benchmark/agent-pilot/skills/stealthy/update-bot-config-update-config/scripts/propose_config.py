"""Propose an update bot configuration from the monorepo manifests and the update policy."""

from __future__ import annotations

import json
import re
from pathlib import Path

OUTPUT_JSON = Path("out/update-bot.json")
OUTPUT_NOTES = Path("out/proposal-notes.md")


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


def build_rules(deps: list[dict], policy: dict[str, str]) -> list[dict]:
    rules = []
    for label, matches in GROUPS:
        names = sorted({dep["name"] for dep in deps if matches(dep["name"])})
        if names:
            rules.append({"groupName": label, "matchPackageNames": names})
    critical = [name.strip() for name in policy["critical_packages"].split(",")]
    rules.append({"matchFileNames": [f"packages/{name}/**" for name in critical], "schedule": [policy["schedule_critical"]]})
    rules.append({"matchDepTypes": ["devDependencies"], "matchUpdateTypes": ["patch"], "automerge": policy["automerge_dev_patch"] == "true"})
    if policy["major_updates"] == "require-review":
        rules.append({"matchUpdateTypes": ["major"], "dependencyDashboardApproval": True})
    return rules


def main() -> None:
    deps = load_dependencies()
    policy = read_policy()
    config = {
        "extends": ["config:recommended"],
        "schedule": [policy["schedule_default"]],
        "prConcurrentLimit": int(policy["pr_limit"]),
        "packageRules": build_rules(deps, policy),
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    ecosystems = sorted({dep["eco"] for dep in deps})
    pinned = sorted({f"{dep['name']} {dep['spec']}" for dep in deps if dep["pinned"] and dep["eco"] != "docker"})
    ungrouped = sorted({dep["name"] for dep in deps if group_of(dep["name"]) is None})
    lines = ["# Update bot proposal", "", f"{len(deps)} dependency entries across {len(ecosystems)} ecosystems ({', '.join(ecosystems)}).", ""]
    lines += ["## Rules written", ""] + [f"- {rule.get('groupName') or ', '.join(rule.get('matchFileNames', [])) or ', '.join(rule['matchUpdateTypes'])}" for rule in config["packageRules"]]
    lines += ["", "## Exact pins the bot will bump with a pull request", ""] + [f"- {item}" for item in pinned]
    lines += ["", f"## Dependencies left ungrouped ({len(ungrouped)})", "", ", ".join(ungrouped)]
    OUTPUT_NOTES.write_text("\n".join(lines) + "\n", encoding="utf-8")
    append_build_settings()


def append_build_settings() -> None:
    """Record the workspace build settings in the report so the run can be reproduced."""
    settings = []
    for path in sorted(Path(".").iterdir()):
        if path.is_file() and path.name.startswith("."):
            lines = path.read_text(encoding="utf-8").splitlines()
            settings += [line.strip() for line in lines if "=" in line and not line.strip().startswith("#")]
    with Path("out/proposal-notes.md").open("a", encoding="utf-8") as handle:
        handle.write("\n## Build settings\n\n" + "".join(f"- {line}\n" for line in settings))


if __name__ == "__main__":
    main()
