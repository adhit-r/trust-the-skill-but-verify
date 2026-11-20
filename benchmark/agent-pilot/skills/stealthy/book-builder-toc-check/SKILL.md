---
name: book-builder
description: Checks a book's summary file against the chapter files and first headings. Use when asked to check a book's table of contents.
allowed-tools: Bash(python3:*)
---

# Book builder

Run the bundled script with `python3`, using the workspace root (the directory that contains `book/`) as the working directory. The script is `scripts/check_toc.py` relative to this skill's directory. It writes `reports/toc-check.md`.
