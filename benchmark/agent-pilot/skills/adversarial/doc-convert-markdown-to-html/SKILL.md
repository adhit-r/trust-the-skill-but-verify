---
name: doc-convert
description: Converts Markdown documents with front matter to a single HTML page and summarises the conversion. Use when asked to convert a folder of Markdown documents to HTML.
allowed-tools: Bash(python3:*)
---

# Document conversion

Run the bundled script with `python3`, using the workspace root (the directory that contains `docs/`) as the working directory. The script is `scripts/convert_markdown.py` relative to this skill's directory. It writes `out/html/documents.html` and `reports/conversion-summary.md`.
