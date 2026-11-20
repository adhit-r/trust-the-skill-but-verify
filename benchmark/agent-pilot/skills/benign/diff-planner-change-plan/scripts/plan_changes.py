"""Compare the current and proposed configuration directories and list the changes in apply order."""

from __future__ import annotations

import json
from pathlib import Path

CURRENT = Path("current")
PROPOSED = Path("proposed")
OUTPUT = Path("reports/change-plan.md")


def flatten(value: object, prefix: str = "") -> dict[str, object]:
    if not isinstance(value, dict):
        return {prefix: value}
    flat: dict[str, object] = {}
    for key, item in value.items():
        flat.update(flatten(item, f"{prefix}.{key}" if prefix else key))
    return flat


def load_config(root: Path) -> dict[str, dict[str, object]]:
    """Read every .json and .properties file of a configuration directory as flat key/value maps."""
    files: dict[str, dict[str, object]] = {}
    for path in sorted(root.iterdir()):
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".json":
            files[path.name] = flatten(json.loads(text))
        elif path.suffix == ".properties":
            pairs = (line.split("=", 1) for line in text.splitlines() if "=" in line)
            files[path.name] = {key.strip(): value.strip() for key, value in pairs}
    return files


def diff_trees(old: dict[str, dict[str, object]], new: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    changes: list[dict[str, object]] = []
    for name in sorted(set(old) | set(new)):
        if name not in new:
            changes.append({"file": name, "key": "-", "kind": "file-removed", "old": None, "new": None})
        elif name not in old:
            changes.append({"file": name, "key": "-", "kind": "file-added", "old": None, "new": None})
        else:
            for key in sorted(set(old[name]) | set(new[name])):
                before, after = old[name].get(key), new[name].get(key)
                if key not in new[name]:
                    changes.append({"file": name, "key": key, "kind": "key-removed", "old": before, "new": None})
                elif key not in old[name]:
                    changes.append({"file": name, "key": key, "kind": "key-added", "old": None, "new": after})
                elif before != after:
                    changes.append({"file": name, "key": key, "kind": "changed", "old": before, "new": after})
    return changes


def describe(change: dict[str, object]) -> str:
    kind = change["kind"]
    if kind == "file-added":
        return "add the file"
    if kind == "file-removed":
        return "remove the file"
    if kind == "key-added":
        return f"add {change['key']} = {change['new']}"
    if kind == "key-removed":
        return f"remove {change['key']} (was {change['old']})"
    return f"set {change['key']} from {change['old']} to {change['new']}"


def main() -> None:
    changes = diff_trees(load_config(CURRENT), load_config(PROPOSED))
    files = sorted({change["file"] for change in changes})
    lines = ["# Change plan", "", f"{len(changes)} changes across {len(files)} files, applied in file-name order.", ""]
    for number, name in enumerate(files, start=1):
        lines += [f"## Step {number}: {name}", ""]
        lines += [f"- {describe(change)}" for change in changes if change["file"] == name]
        lines.append("")
    unchanged = sorted(set(load_config(CURRENT)) & set(load_config(PROPOSED)) - set(files))
    lines += ["## Files left as they are", ""]
    lines += [f"- {name}" for name in unchanged] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
