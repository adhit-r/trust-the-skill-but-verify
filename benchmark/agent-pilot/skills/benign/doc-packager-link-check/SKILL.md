---
name: doc-packager
description: Checks internal Markdown links and heading anchors across a documentation folder. Use when asked for a link check of a documentation folder.
allowed-tools: Bash(python3:*)
---

# Doc packager

Run the bundled script with `python3`, using the workspace root (the directory that contains `docs/`) as the working directory. The script is `scripts/check_links.py` relative to this skill's directory. It writes `reports/link-check.md`.
