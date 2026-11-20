---
name: doc-partition
description: Outlines the heading hierarchy of each document and flags skipped heading levels. Use when asked for a heading outline of long-form Markdown documents.
allowed-tools: Bash(python3:*)
---

# Document partition

Run the bundled script with `python3`, using the workspace root (the directory that contains `corpus/`) as the working directory. The script is `scripts/outline_headings.py` relative to this skill's directory. It writes `reports/heading-hierarchy.md`.
