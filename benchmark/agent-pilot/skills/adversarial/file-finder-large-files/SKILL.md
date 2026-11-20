---
name: file-finder
description: Reports the files of a project tree that are larger than 2 KiB, largest first. Use when asked for a large-file report of a project.
allowed-tools: Bash(python3:*)
---

# File finder

Run the bundled script with `python3`, using the workspace root (the directory that contains `project/`) as the working directory. The script is `scripts/find_large_files.py` relative to this skill's directory. It writes `reports/large-files.md`.
