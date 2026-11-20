---
name: text-extract
description: Extracts invoice line items from text dumps of invoices into a CSV file. Use when asked for a line-item CSV of the invoices in a folder.
allowed-tools: Bash(python3:*)
---

# Text extract

Run the bundled script with `python3`, using the workspace root (the directory that contains `docs/`) as the working directory. The script is `scripts/extract_line_items.py` relative to this skill's directory. It writes `out/line-items.csv`.
