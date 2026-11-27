---
name: tabular-privacy
description: Finds groups smaller than k across quasi-identifier columns in CSV exports. Use when asked for a k-anonymity or small-group check on customer exports.
allowed-tools: Bash(python3:*)
---

# Tabular privacy

Run the bundled script with `python3`, using the workspace root (the directory that contains `data/`) as the working directory. The script is `scripts/check_k_anonymity.py` relative to this skill's directory. It writes `reports/k-anonymity.md`.
