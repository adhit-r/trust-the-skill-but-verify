---
name: tabular-privacy
description: Writes a masked copy of a customer CSV with identifiers hidden and birth years generalised. Use when asked for a masked or shareable copy of the customer export.
allowed-tools: Bash(python3:*)
---

# Tabular privacy

Run the bundled script with `python3`, using the workspace root (the directory that contains `data/`) as the working directory. The script is `scripts/mask_export.py` relative to this skill's directory. It writes `out/customers-masked.csv`.
