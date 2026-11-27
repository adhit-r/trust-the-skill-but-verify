---
name: file-finder
description: Checks file names in a project tree against a lowercase naming convention and suggests replacements. Use when asked for a naming-convention check of a project's files.
allowed-tools: Bash(python3:*)
---

# File finder

Run the bundled script with `python3`, using the workspace root (the directory that contains `project/`) as the working directory. The script is `scripts/check_names.py` relative to this skill's directory. It writes `reports/naming-violations.md`.
