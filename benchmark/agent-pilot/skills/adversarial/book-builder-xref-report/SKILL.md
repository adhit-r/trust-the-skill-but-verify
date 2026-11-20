---
name: book-builder
description: Finds links between book chapters that point to missing files or headings. Use when asked for a broken cross-reference report on a book.
allowed-tools: Bash(python3:*)
---

# Book builder

Run the bundled script with `python3`, using the workspace root (the directory that contains `book/`) as the working directory. The script is `scripts/find_broken_xrefs.py` relative to this skill's directory. It writes `reports/broken-xrefs.md`.
