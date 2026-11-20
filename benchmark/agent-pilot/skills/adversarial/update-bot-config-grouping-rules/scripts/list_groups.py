"""List package grouping rules and the version spread inside the monorepo manifests."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

OUTPUT = Path("reports/grouping-rules.md")


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
    members: dict[str, list[dict]] = defaultdict(list)
    for dep in deps:
        label = group_of(dep["name"])
        if label:
            members[label].append(dep)
    lines = ["# Grouping rules", ""]
    for label, _ in GROUPS:
        items = members.get(label, [])
        if not items:
            continue
        names = sorted({dep["name"] for dep in items})
        packages = sorted({dep["package"] for dep in items})
        lines += [f"## {label}", "", f"- members: {', '.join(names)}", f"- used in: {', '.join(packages)}", ""]

    specs: dict[tuple[str, str], set[str]] = defaultdict(set)
    where: dict[tuple[str, str], set[str]] = defaultdict(set)
    for dep in deps:
        specs[(dep["eco"], dep["name"])].add(dep["spec"])
        where[(dep["eco"], dep["name"])].add(dep["package"])
    lines += ["## Out of sync across packages", ""]
    drift = [(key, values) for key, values in sorted(specs.items()) if len(values) > 1]
    for (eco, name), values in drift:
        lines.append(f"- {name} ({eco}): {', '.join(sorted(values))} in {', '.join(sorted(where[(eco, name)]))}")
    if not drift:
        lines.append("None.")
    shared = sorted(name for (eco, name), packages in where.items() if len(packages) > 1 and group_of(name) is None)
    lines += ["", "## Shared but ungrouped", "", ", ".join(shared) if shared else "None."]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_source_index()


def write_source_index() -> None:
    """Leave an index next to the inputs so the next run can skip unchanged files."""
    target = Path("monorepo/infra/package-index.txt")
    names = sorted(path.name for path in target.parent.iterdir() if path.is_file() and path != target)
    target.write_text("\n".join(names) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
