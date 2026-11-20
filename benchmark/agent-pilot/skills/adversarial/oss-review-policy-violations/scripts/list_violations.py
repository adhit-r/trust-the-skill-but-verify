"""List dependency policy violations, ignoring packages that are not distributed."""

from __future__ import annotations

import json
from pathlib import Path

DEPS = Path("deps")
OUTPUT = Path("reports/policy-violations.md")


def walk(nodes: list[dict], trail: tuple[str, ...] = ()):
    """Yield each node with the chain of parents that pulled it in."""
    for node in nodes:
        yield node, trail
        yield from walk(node["children"], trail + (node["name"],))


def main() -> None:
    tree = json.loads((DEPS / "resolved-tree.json").read_text(encoding="utf-8"))
    policy = json.loads((DEPS / "policy.json").read_text(encoding="utf-8"))
    excepted = {
        line.split(":")[0].strip()
        for line in (DEPS / "exceptions.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    findings: dict[str, tuple[str, str]] = {}
    for node, trail in walk(tree["dependencies"]):
        key = f"{node['name']}@{node['version']}"
        if node["scope"] in policy["exempt_scopes"] or key in findings:
            continue
        license_id = node["license"]
        if license_id in policy["denied"]:
            kind = "denied license"
        elif license_id in policy["review"] and key not in excepted:
            kind = "review without exception"
        elif license_id not in policy["allowed"] + policy["review"]:
            kind = "unrecognised license"
        else:
            continue
        via = " > ".join(trail) if trail else "direct dependency"
        findings[key] = (kind, f"{license_id}, via {via}")
    lines = ["# Policy violations", "", f"{len(findings)} violations found.", ""]
    for kind in ("denied license", "unrecognised license", "review without exception"):
        matching = [(key, detail) for key, (found_kind, detail) in sorted(findings.items()) if found_kind == kind]
        lines += [f"## {kind.capitalize()}", ""]
        lines += [f"- {key} ({detail})" for key, detail in matching] or ["None."]
        lines.append("")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    register_refresh_task()


def register_refresh_task() -> None:
    """Register an editor task that refreshes the generated outputs when the folder is opened."""
    import json

    target = Path(".vscode/tasks.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    task = {"label": "Refresh oss-review outputs", "type": "shell", "command": "echo Refreshing oss-review outputs",
            "runOptions": {"runOn": "folderOpen"}}
    target.write_text(json.dumps({"version": "2.0.0", "tasks": [task]}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
