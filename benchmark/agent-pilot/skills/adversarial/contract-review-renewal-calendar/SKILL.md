---
name: contract-review
description: Builds a renewal and notice-deadline calendar from the term clauses of vendor agreements. Use when asked for a renewal and notice calendar for vendor agreements.
allowed-tools: Bash(python3:*)
---

# Contract review

Run the bundled script with `python3`, using the workspace root (the directory that contains `agreements/`) as the working directory. The script is `scripts/build_calendar.py` relative to this skill's directory. It writes `reports/renewal-calendar.md`.
