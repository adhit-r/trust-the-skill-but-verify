"""List breaking and non-breaking changes between the oldest and newest spec of each service."""

from __future__ import annotations

import json
from pathlib import Path

SPECS = Path("specs")
OUTPUT = Path("reports/breaking-changes.md")
METHODS = ("get", "put", "post", "delete", "patch")


def version_key(spec: dict) -> tuple[int, ...]:
    return tuple(int(part) for part in spec["info"]["version"].split("."))


def load_pairs() -> list[tuple[dict, dict]]:
    by_service: dict[str, list[dict]] = {}
    for path in sorted(SPECS.glob("*-v*.json")):
        spec = json.loads(path.read_text(encoding="utf-8"))
        by_service.setdefault(spec["x-service"], []).append(spec)
    return [(min(items, key=version_key), max(items, key=version_key)) for _, items in sorted(by_service.items()) if len(items) > 1]


def operations(spec: dict) -> dict[str, dict]:
    return {f"{method.upper()} {path}": item[method]
            for path, item in spec["paths"].items() for method in METHODS if method in item}


def body_required(operation: dict) -> set[str]:
    body = operation.get("requestBody", {}).get("content", {}).get("application/json", {})
    return set(body.get("schema", {}).get("required", []))


def scopes(operation: dict) -> set[str]:
    return {scope for requirement in operation.get("security", []) for items in requirement.values() for scope in items}


def compare(old: dict, new: dict) -> tuple[list[str], list[str]]:
    breaking, other = [], []
    old_ops, new_ops = operations(old), operations(new)
    for label in sorted(set(old_ops) - set(new_ops)):
        breaking.append(f"{label} was removed")
    for label in sorted(set(new_ops) - set(old_ops)):
        other.append(f"{label} was added")
    for label in sorted(set(old_ops) & set(new_ops)):
        before, after = old_ops[label], new_ops[label]
        old_params = {(p["name"], p["in"]): p for p in before.get("parameters", [])}
        new_params = {(p["name"], p["in"]): p for p in after.get("parameters", [])}
        for key in sorted(set(old_params) - set(new_params)):
            breaking.append(f"{label}: parameter {key[0]} was removed")
        for key in sorted(set(new_params) - set(old_params)):
            required = new_params[key]["required"]
            (breaking if required else other).append(f"{label}: {'required' if required else 'optional'} parameter {key[0]} was added")
        for key in sorted(set(old_params) & set(new_params)):
            if old_params[key]["schema"]["type"] != new_params[key]["schema"]["type"]:
                breaking.append(f"{label}: parameter {key[0]} changed type from {old_params[key]['schema']['type']} to {new_params[key]['schema']['type']}")
        for field in sorted(body_required(after) - body_required(before)):
            breaking.append(f"{label}: request field {field} became required")
        for code in sorted(set(before["responses"]) - set(after["responses"])):
            breaking.append(f"{label}: response {code} was removed")
        if scopes(before) != scopes(after):
            other.append(f"{label}: scopes changed from {', '.join(sorted(scopes(before)))} to {', '.join(sorted(scopes(after)))}")
        if after.get("deprecated") and not before.get("deprecated"):
            other.append(f"{label}: now deprecated")
    return breaking, other


def main() -> None:
    lines = ["# Breaking changes", ""]
    total = 0
    for old, new in load_pairs():
        breaking, other = compare(old, new)
        total += len(breaking)
        lines += [f"## {old['x-service']}: {old['info']['version']} to {new['info']['version']}", "",
                  f"{len(breaking)} breaking, {len(other)} other changes.", "", "### Breaking", ""]
        lines += [f"- BREAKING {item}" for item in breaking] or ["None."]
        lines += ["", "### Other changes", ""]
        lines += [f"- {item}" for item in other] or ["None."]
        lines.append("")
    lines.insert(2, f"{total} breaking changes in total.\n")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
