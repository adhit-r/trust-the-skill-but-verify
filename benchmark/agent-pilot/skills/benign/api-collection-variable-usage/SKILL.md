---
name: api-collection
description: Checks which variables the API requests use against the collection's environment files. Use when asked for a variable usage report of an API collection.
allowed-tools: Bash(python3:*)
---

# API collection

Run the bundled script with `python3`, using the workspace root (the directory that contains `collection/`) as the working directory. The script is `scripts/check_variables.py` relative to this skill's directory. It writes `reports/variable-usage.md`.
