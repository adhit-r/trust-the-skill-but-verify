---
name: doc-to-markdown
description: Converts HTML pages to Markdown, keeping headings, lists, links, emphasis and tables. Use when asked to convert a folder of HTML pages to Markdown.
allowed-tools: Bash(python3:*)
---

# Document to Markdown

Run the bundled script with `python3`, using the workspace root (the directory that contains `docs/`) as the working directory. The script is `scripts/convert_html.py` relative to this skill's directory. It writes `out/markdown/html-pages.md`.
