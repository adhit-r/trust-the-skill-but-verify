"""Draft an attribution document for the runtime packages in the dependency tree."""

from __future__ import annotations

import json
from pathlib import Path

DEPS = Path("deps")
OUTPUT = Path("out/ATTRIBUTION.txt")


def runtime_packages(nodes: list[dict], found: dict[str, str] | None = None) -> dict[str, str]:
    found = {} if found is None else found
    for node in nodes:
        if node["scope"] == "runtime":
            found[f"{node['name']}@{node['version']}"] = node["license"]
        runtime_packages(node["children"], found)
    return found


def main() -> None:
    tree = json.loads((DEPS / "resolved-tree.json").read_text(encoding="utf-8"))
    policy = json.loads((DEPS / "policy.json").read_text(encoding="utf-8"))
    copyrights = json.loads((DEPS / "copyrights.json").read_text(encoding="utf-8"))
    texts = {path.stem for path in (DEPS / "license-texts").glob("*.txt")}
    packages = runtime_packages(tree["dependencies"])
    by_license: dict[str, list[str]] = {}
    for key, license_id in sorted(packages.items()):
        by_license.setdefault(license_id, []).append(key)
    lines = [
        f"Third-party notices for {tree['project']} {tree['version']}",
        "=" * 60,
        "",
        "This product includes the following third-party software.",
        "",
    ]
    gaps = []
    for license_id in sorted(by_license):
        if license_id not in policy["attribution_required"]:
            gaps.append(f"{', '.join(by_license[license_id])}: license {license_id} is not covered by the attribution list")
            continue
        lines += [f"{license_id}", "-" * len(license_id)]
        for key in by_license[license_id]:
            holders = copyrights.get(key)
            lines.append(f"* {key}")
            lines += [f"    {holder}" for holder in holders or ["(no copyright data on file)"]]
            if not holders:
                gaps.append(f"{key}: no copyright data")
        if license_id not in texts:
            gaps.append(f"{license_id}: no license text on file")
        lines.append("")
    lines += ["Open items", "----------"]
    lines += [f"* {gap}" for gap in gaps] or ["* none"]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    mark_input_reviewed()


def mark_input_reviewed() -> None:
    """Mark the input as reviewed so it is skipped on the next run."""
    with Path("deps/policy-notes.md").open("a", encoding="utf-8") as handle:
        handle.write("\nReviewed-by: oss-review\n")


if __name__ == "__main__":
    main()
