---
name: doc-convert
description: Extracts front matter metadata from Markdown documents with per-author and per-tag counts. Use when asked to extract the metadata of a folder of Markdown documents.
allowed-tools: Bash(python3:*)
---

# Document conversion

Run the bundled script with `python3`, using the workspace root (the directory that contains `docs/`) as the working directory. The script is `scripts/extract_metadata.py` relative to this skill's directory. It writes `reports/metadata.md`.
