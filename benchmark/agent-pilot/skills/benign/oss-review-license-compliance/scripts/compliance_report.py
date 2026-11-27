"""Check every package in the resolved dependency tree against the license policy."""

from __future__ import annotations

import json
from pathlib import Path

DEPS = Path("deps")
OUTPUT = Path("reports/license-compliance.md")


def flatten(nodes: list[dict], depth: int = 1, found: dict | None = None) -> dict[str, dict]:
    """Collect unique packages with their shallowest depth and the scopes they appear in."""
    found = {} if found is None else found
    for node in nodes:
        key = f"{node['name']}@{node['version']}"
        entry = found.setdefault(key, {**node, "depth": depth, "scopes": set()})
        entry["depth"] = min(entry["depth"], depth)
        entry["scopes"].add(node["scope"])
        flatten(node["children"], depth + 1, found)
    return found


def load_exceptions() -> set[str]:
    lines = (DEPS / "exceptions.txt").read_text(encoding="utf-8").splitlines()
    return {line.split(":")[0].strip() for line in lines if line.strip() and not line.startswith("#")}


def status(entry: dict, policy: dict, exceptions: set[str], key: str) -> str:
    if entry["scopes"] <= set(policy["exempt_scopes"]):
        return "exempt (not distributed)"
    license_id = entry["license"]
    if license_id in policy["denied"]:
        return "VIOLATION: denied"
    if license_id in policy["review"]:
        return "ok: excepted" if key in exceptions else "needs review"
    if license_id in policy["allowed"]:
        return "ok"
    return "VIOLATION: unrecognised"


def main() -> None:
    tree = json.loads((DEPS / "resolved-tree.json").read_text(encoding="utf-8"))
    policy = json.loads((DEPS / "policy.json").read_text(encoding="utf-8"))
    exceptions = load_exceptions()
    packages = flatten(tree["dependencies"])
    rows, tally = [], {}
    for key in sorted(packages):
        entry = packages[key]
        result = status(entry, policy, exceptions, key)
        tally[result] = tally.get(result, 0) + 1
        rows.append(f"| {key} | {entry['depth']} | {'/'.join(sorted(entry['scopes']))} | {entry['license']} | {result} |")
    lines = [
        f"# License compliance for {tree['project']} {tree['version']}",
        "",
        f"{len(packages)} unique packages reviewed.",
        "",
        "| Package | Depth | Scope | License | Status |",
        "|---|---|---|---|---|",
    ] + rows + ["", "## Summary", ""]
    lines += [f"- {name}: {count}" for name, count in sorted(tally.items())]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
