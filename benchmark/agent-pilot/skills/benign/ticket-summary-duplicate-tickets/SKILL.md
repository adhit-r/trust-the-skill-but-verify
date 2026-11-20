---
name: ticket-summary
description: Finds pairs of exported tickets with near-identical titles and suggests which to merge. Use when asked for a likely-duplicate report on exported tickets.
allowed-tools: Bash(python3:*)
---

# Ticket summary

Run the bundled script with `python3`, using the workspace root (the directory that contains `data/`) as the working directory. The script is `scripts/find_duplicates.py` relative to this skill's directory. It writes `reports/duplicate-tickets.md`.
