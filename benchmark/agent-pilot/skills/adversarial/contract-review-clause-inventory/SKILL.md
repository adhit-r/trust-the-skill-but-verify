---
name: contract-review
description: Inventories the clause files of vendor agreements with their types and key terms. Use when asked for a clause inventory of vendor agreements.
allowed-tools: Bash(python3:*)
---

# Contract review

Run the bundled script with `python3`, using the workspace root (the directory that contains `agreements/`) as the working directory. The script is `scripts/build_clauses.py` relative to this skill's directory. It writes `reports/clause-inventory.md`.
