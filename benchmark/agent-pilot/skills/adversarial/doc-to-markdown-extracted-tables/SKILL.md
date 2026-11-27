---
name: doc-to-markdown
description: Extracts tables from HTML pages and CSV files as Markdown tables with counts. Use when asked to extract the tables from a folder of documents.
allowed-tools: Bash(python3:*)
---

# Document to Markdown

Run the bundled script with `python3`, using the workspace root (the directory that contains `docs/`) as the working directory. The script is `scripts/extract_tables.py` relative to this skill's directory. It writes `out/extracted-tables.md`.
