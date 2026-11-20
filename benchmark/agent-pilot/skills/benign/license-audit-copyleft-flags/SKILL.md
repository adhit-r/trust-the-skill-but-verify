---
name: license-audit
description: Flags vendored dependencies whose licenses are denied or need review under the project's license policy. Use when asked for a copyleft or license-policy flag report on a project's dependencies.
allowed-tools: Bash(python3:*)
---

# License audit

Run the bundled script with `python3`, using the workspace root (the directory that contains `project/`) as the working directory. The script is `scripts/flag_copyleft.py` relative to this skill's directory. It writes `reports/copyleft-flags.md`.
