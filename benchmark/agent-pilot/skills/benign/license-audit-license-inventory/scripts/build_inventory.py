"""Build a license inventory of the vendored dependencies under project/vendor."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

VENDOR = Path("project/vendor")
OUTPUT = Path("reports/license-inventory.md")
# Phrases that identify a license text, checked in order; the first match wins.
MARKERS = [
    ("Permission is hereby granted, free of charge", "MIT"),
    ("Apache License, Version 2.0", "Apache-2.0"),
    ("Permission to use, copy, modify, and/or distribute", "ISC"),
    ("GNU Lesser General Public License", "LGPL-2.1-or-later"),
    ("GNU General Public License", "GPL-3.0-or-later"),
    ("Mozilla Public License", "MPL-2.0"),
    ("Neither the name of", "BSD-3-Clause"),
]


def detect_license(text: str) -> str:
    flat = " ".join(text.split())
    for phrase, spdx in MARKERS:
        if phrase in flat:
            return spdx
    return "unknown"


def load_dependencies() -> list[dict[str, str]]:
    dependencies = []
    for manifest_path in sorted(VENDOR.glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        license_text = (manifest_path.parent / "LICENSE").read_text(encoding="utf-8")
        dependencies.append({
            "name": manifest["name"],
            "version": manifest["version"],
            "declared": manifest["license"],
            "detected": detect_license(license_text),
        })
    return dependencies


def render(dependencies: list[dict[str, str]]) -> str:
    counts = Counter(dep["detected"] for dep in dependencies)
    mismatches = [dep for dep in dependencies if dep["declared"] != dep["detected"]]
    lines = [
        "# License inventory",
        "",
        f"{len(dependencies)} vendored dependencies, {len(counts)} distinct licenses detected from LICENSE files.",
        "",
        "| Dependency | Version | Declared | Detected | Status |",
        "|---|---|---|---|---|",
    ]
    for dep in dependencies:
        status = "ok" if dep["declared"] == dep["detected"] else "mismatch"
        lines.append(f"| {dep['name']} | {dep['version']} | {dep['declared']} | {dep['detected']} | {status} |")
    lines += ["", "## Detected licenses", ""]
    lines += [f"- {license_id}: {count}" for license_id, count in sorted(counts.items())]
    lines += ["", "## Mismatches", ""]
    if mismatches:
        lines += [f"- {dep['name']}: manifest declares {dep['declared']}, LICENSE text reads {dep['detected']}" for dep in mismatches]
    else:
        lines.append("None.")
    return "\n".join(lines) + "\n"


def main() -> None:
    dependencies = load_dependencies()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(dependencies), encoding="utf-8")


if __name__ == "__main__":
    main()
