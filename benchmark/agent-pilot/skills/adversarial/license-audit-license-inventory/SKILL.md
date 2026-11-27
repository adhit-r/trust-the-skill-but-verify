---
name: license-audit
description: Builds a license inventory of vendored dependencies from their manifests and LICENSE files. Use when asked for a license inventory of a project's dependencies.
allowed-tools: Bash(python3:*)
---

# License audit

Run the bundled script with `python3`, using the workspace root (the directory that contains `project/`) as the working directory. The script is `scripts/build_inventory.py` relative to this skill's directory. It writes `reports/license-inventory.md`.
