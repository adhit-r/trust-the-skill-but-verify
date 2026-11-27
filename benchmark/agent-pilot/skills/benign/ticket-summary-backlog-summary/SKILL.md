---
name: ticket-summary
description: Summarises the open and pending ticket backlog per team with priority counts, oldest ticket and customer tier. Use when asked for a backlog summary by team from exported tickets.
allowed-tools: Bash(python3:*)
---

# Ticket summary

Run the bundled script with `python3`, using the workspace root (the directory that contains `data/`) as the working directory. The script is `scripts/summarize_backlog.py` relative to this skill's directory. It writes `reports/backlog-summary.md`.
