---
name: doc-packager
description: Generates a linked table of contents from the headings of a Markdown documentation folder. Use when asked for a table of contents of a documentation folder.
allowed-tools: Bash(python3:*)
---

# Doc packager

Run the bundled script with `python3`, using the workspace root (the directory that contains `docs/`) as the working directory. The script is `scripts/build_toc.py` relative to this skill's directory. It writes `out/toc.md`.
