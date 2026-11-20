---
name: pii-redact
description: Inventories the personal data types in support tickets with counts per type and the policy action. Use when asked for a PII inventory of a folder of support tickets.
allowed-tools: Bash(python3:*)
---

# PII redact

Run the bundled script with `python3`, using the workspace root (the directory that contains `tickets/`) as the working directory. The script is `scripts/inventory_pii.py` relative to this skill's directory. It writes `reports/pii-inventory.md`.
