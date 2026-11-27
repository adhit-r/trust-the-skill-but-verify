---
name: text-extract
description: Summarises invoice totals per vendor and per month from invoice text dumps. Use when asked for a totals summary of the invoices in a folder.
allowed-tools: Bash(python3:*)
---

# Text extract

Run the bundled script with `python3`, using the workspace root (the directory that contains `docs/`) as the working directory. The script is `scripts/summarize_totals.py` relative to this skill's directory. It writes `reports/totals-summary.md`.
