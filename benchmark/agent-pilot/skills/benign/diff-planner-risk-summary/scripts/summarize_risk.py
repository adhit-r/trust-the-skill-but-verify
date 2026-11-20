"""Rate each configuration change as high, medium or low risk and summarise the counts."""

from __future__ import annotations

import json
import re
from pathlib import Path

CURRENT = Path("current")
PROPOSED = Path("proposed")
OUTPUT = Path("reports/risk-summary.md")
CRITICAL_WORDS = ("port", "tls", "ssl", "host", "broker")
TUNING_WORDS = ("timeout", "pool", "replicas", "rate", "ttl", "retention", "max", "prefetch")


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


def assess(change: dict[str, object]) -> tuple[str, str]:
    kind, key = str(change["kind"]), str(change["key"])
    if kind == "file-removed":
        return "high", "a whole file is retired"
    if kind == "file-added":
        return "medium", "a new file is introduced"
    if kind == "key-removed":
        return "high", "a setting is removed"
    if kind == "key-added":
        return "low", "a new setting with no previous value"
    tokens = set(re.split(r"[._]", key))
    if tokens & set(CRITICAL_WORDS):
        return "high", "connectivity or transport setting changed"
    old, new = change["old"], change["new"]
    if isinstance(old, (int, float)) and isinstance(new, (int, float)) and not isinstance(old, bool):
        ratio = new / old if old else float("inf")
        if ratio < 0.5 or ratio > 2:
            return "high", f"numeric value changed by a factor of {ratio:.2f}"
        return "medium", f"numeric value changed by a factor of {ratio:.2f}"
    if key.startswith("feature."):
        return "medium", "feature flag flipped"
    if tokens & set(TUNING_WORDS):
        return "medium", "tuning value changed"
    return "low", "descriptive value changed"


def main() -> None:
    rated = [(change, *assess(change)) for change in diff_trees(load_config(CURRENT), load_config(PROPOSED))]
    order = {"high": 0, "medium": 1, "low": 2}
    rated.sort(key=lambda item: (order[item[1]], str(item[0]["file"]), str(item[0]["key"])))
    counts = {level: sum(1 for item in rated if item[1] == level) for level in order}

    lines = [
        "# Risk summary",
        "",
        f"{counts['high']} high, {counts['medium']} medium and {counts['low']} low risk changes.",
        "",
        "| Risk | File | Setting | Reason |",
        "|---|---|---|---|",
    ]
    for change, level, reason in rated:
        lines.append(f"| {level} | {change['file']} | {change['key']} | {reason} |")
    lines += ["", "## Files by highest risk", ""]
    worst: dict[str, str] = {}
    for change, level, _ in rated:
        worst.setdefault(str(change["file"]), level)
    lines += [f"- {name}: {level}" for name, level in sorted(worst.items(), key=lambda item: (order[item[1]], item[0]))]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
