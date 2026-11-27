---
name: doc-to-markdown
description: Builds an index of documents with format, size, line count, title and table shape. Use when asked for an index or inventory of the documents in a folder.
allowed-tools: Bash(python3:*)
---

# Document to Markdown

Run the bundled script with `python3`, using the workspace root (the directory that contains `docs/`) as the working directory. The script is `scripts/build_index.py` relative to this skill's directory. It writes `reports/conversion-index.md`.
