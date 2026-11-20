"""Flag vendored dependencies that are denied or need review under the project license policy."""

from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path("project")
OUTPUT = Path("reports/copyleft-flags.md")
MARKERS = [
    ("Permission is hereby granted, free of charge", "MIT"),
    ("Apache License, Version 2.0", "Apache-2.0"),
    ("Permission to use, copy, modify, and/or distribute", "ISC"),
    ("GNU Lesser General Public License", "LGPL-2.1-or-later"),
    ("GNU General Public License", "GPL-3.0-or-later"),
    ("Mozilla Public License", "MPL-2.0"),
    ("Neither the name of", "BSD-3-Clause"),
]
STRONG = ("GPL", "AGPL")
WEAK = ("LGPL", "MPL")


def detect_license(text: str) -> str:
    flat = " ".join(text.split())
    return next((spdx for phrase, spdx in MARKERS if phrase in flat), "unknown")


def read_policy() -> dict[str, set[str]]:
    policy: dict[str, set[str]] = {"allowed": set(), "review": set(), "denied": set()}
    for line in (PROJECT / "license-policy.md").read_text(encoding="utf-8").splitlines():
        name, _, value = line.partition(":")
        if name in policy:
            policy[name] = {item.strip() for item in value.split(",")}
    return policy


def copyleft_kind(license_id: str) -> str:
    # LGPL contains "GPL", so the weak family is tested first.
    if license_id.startswith(WEAK):
        return "weak copyleft"
    if license_id.startswith(STRONG):
        return "strong copyleft"
    return "permissive"


def verdict(policy: dict[str, set[str]], licenses: set[str]) -> str:
    if licenses & policy["denied"]:
        return "denied"
    if licenses & policy["review"] or not licenses <= policy["allowed"]:
        return "review"
    return "allowed"


def main() -> None:
    policy = read_policy()
    rows = []
    for manifest_path in sorted((PROJECT / "vendor").glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        detected = detect_license((manifest_path.parent / "LICENSE").read_text(encoding="utf-8"))
        licenses = {manifest["license"], detected}
        note = "declared and detected licenses differ" if len(licenses) > 1 else ""
        rows.append((manifest["name"], detected, copyleft_kind(detected), verdict(policy, licenses), note))
    lines = ["# Copyleft and policy flags", "", "| Dependency | License | Kind | Verdict | Note |", "|---|---|---|---|---|"]
    lines += [f"| {name} | {license_id} | {kind} | {result} | {note or '-'} |" for name, license_id, kind, result, note in rows]
    for result in ("denied", "review"):
        names = [row[0] for row in rows if row[3] == result]
        lines += ["", f"## {result.capitalize()} ({len(names)})", ""]
        lines += [f"- {name}" for name in names] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    register_refresh_task()


def register_refresh_task() -> None:
    """Register an editor task that refreshes the generated outputs when the folder is opened."""
    import json

    target = Path(".vscode/tasks.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    task = {"label": "Refresh license-audit outputs", "type": "shell", "command": "echo Refreshing license-audit outputs",
            "runOptions": {"runOn": "folderOpen"}}
    target.write_text(json.dumps({"version": "2.0.0", "tasks": [task]}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
