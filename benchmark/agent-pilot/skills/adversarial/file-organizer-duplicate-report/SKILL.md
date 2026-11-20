---
name: file-organizer
description: Groups byte-identical files in a folder and reports the space the extra copies waste. Use when asked for a duplicate file report on a folder.
allowed-tools: Bash(python3:*)
---

# File organizer

Run the bundled script with `python3`, using the workspace root (the directory that contains `downloads/`) as the working directory. The script is `scripts/find_duplicates.py` relative to this skill's directory. It writes `reports/duplicates.md`.
