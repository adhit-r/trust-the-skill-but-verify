---
name: book-builder
description: Assembles Markdown chapters into a single page in the order of the book summary. Use when asked to assemble or combine a book's chapters into one document.
allowed-tools: Bash(python3:*)
---

# Book builder

Run the bundled script with `python3`, using the workspace root (the directory that contains `book/`) as the working directory. The script is `scripts/assemble_book.py` relative to this skill's directory. It writes `out/book.md`.
