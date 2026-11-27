"""Draft a third-party NOTICE file from the vendored dependencies that the license policy lets ship."""

from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path("project")
OUTPUT = Path("out/NOTICE.txt")
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
    return next((spdx for phrase, spdx in MARKERS if phrase in flat), "unknown")


def denied_licenses() -> set[str]:
    for line in (PROJECT / "license-policy.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("denied:"):
            return {item.strip() for item in line.removeprefix("denied:").split(",")}
    return set()


def copyright_line(text: str) -> str:
    for line in text.splitlines():
        if "copyright" in line.lower() and ("(c)" in line.lower() or line.strip().lower().startswith("copyright")):
            return line.strip()
    return "Copyright holder not stated"


def main() -> None:
    denied = denied_licenses()
    header = (PROJECT / "notice-header.txt").read_text(encoding="utf-8").rstrip("\n")
    listed: list[str] = []
    held_back: list[str] = []
    for manifest_path in sorted((PROJECT / "vendor").glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        license_text = (manifest_path.parent / "LICENSE").read_text(encoding="utf-8")
        detected = detect_license(license_text)
        if detected in denied or manifest["license"] in denied:
            held_back.append(f"{manifest['name']} {manifest['version']} ({detected})")
            continue
        listed.append(
            f"{manifest['name']} {manifest['version']}\n"
            f"  {copyright_line(license_text)}\n"
            f"  License: {detected}\n"
            f"  Source: {manifest['homepage']}"
        )
    lines = [header, "", "=" * 60, ""]
    lines.append("\n\n".join(listed))
    lines += ["", "=" * 60, "", "Not listed because the license policy denies the license:"]
    lines += [f"  - {item}" for item in held_back] or ["  none"]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
