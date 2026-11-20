"""Write rollback notes that undo the proposed configuration changes in reverse order."""

from __future__ import annotations

import json
import re
from pathlib import Path

CURRENT = Path("current")
PROPOSED = Path("proposed")
OUTPUT = Path("out/rollback-notes.txt")
RESTART_WORDS = ("port", "tls", "ssl", "host", "broker")


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


def undo(change: dict[str, object]) -> str:
    kind, name, key = change["kind"], change["file"], change["key"]
    if kind == "file-added":
        return f"delete {name}"
    if kind == "file-removed":
        return f"restore {name} from the current directory"
    if kind == "key-added":
        return f"in {name}, remove {key}"
    if kind == "key-removed":
        return f"in {name}, restore {key} = {change['old']}"
    return f"in {name}, restore {key} = {change['old']} (proposed value {change['new']})"


def main() -> None:
    changes = diff_trees(load_config(CURRENT), load_config(PROPOSED))
    restart = sorted({str(c["file"]) for c in changes if set(re.split(r"[._]", str(c["key"]))) & set(RESTART_WORDS)})
    lines = [
        "Rollback notes",
        "==============",
        "",
        f"{len(changes)} changes to undo. Work through the steps in this order, last change first.",
        "",
    ]
    for number, change in enumerate(reversed(changes), start=1):
        lines.append(f"{number}. {undo(change)}")
    lines += ["", "Restart needed after restoring:"]
    lines += [f"  - {name}" for name in restart] or ["  - none"]
    lines += ["", "Verify: compare the restored files with the current directory; no differences should remain."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
