---
name: content-extract
description: Builds a metadata catalog of mixed Markdown, HTML, CSV, JSON, text and log files with type, size, line count, title, author and date. Use when asked for a metadata catalog of a folder of mixed documents.
allowed-tools: Bash(python3:*)
---

# Content extract

Run the bundled script with `python3`, using the workspace root (the directory that contains `samples/`) as the working directory. The script is `scripts/catalog_metadata.py` relative to this skill's directory. It writes `reports/metadata-catalog.md`.
