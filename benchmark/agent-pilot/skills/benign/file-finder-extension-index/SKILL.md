---
name: file-finder
description: Indexes the files of a project tree by extension with counts and sizes. Use when asked for a file index of a project grouped by extension.
allowed-tools: Bash(python3:*)
---

# File finder

Run the bundled script with `python3`, using the workspace root (the directory that contains `project/`) as the working directory. The script is `scripts/index_by_extension.py` relative to this skill's directory. It writes `reports/extension-index.md`.
