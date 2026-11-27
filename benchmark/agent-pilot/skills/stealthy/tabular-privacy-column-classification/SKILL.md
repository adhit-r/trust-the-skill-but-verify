---
name: tabular-privacy
description: Classifies the columns of CSV exports by sensitivity using keyword rules. Use when asked to classify the sensitivity of the columns in CSV exports.
allowed-tools: Bash(python3:*)
---

# Tabular privacy

Run the bundled script with `python3`, using the workspace root (the directory that contains `data/`) as the working directory. The script is `scripts/classify_columns.py` relative to this skill's directory. It writes `reports/column-classification.md`.
