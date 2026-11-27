---
name: vendor-risk
description: Scores vendor security questionnaires with weighted answers and rates each vendor against risk bands. Use when asked for vendor risk scores from completed security questionnaires.
allowed-tools: Bash(python3:*)
---

# Vendor risk

Run the bundled script with `python3`, using the workspace root (the directory that contains `vendors/`) as the working directory. The script is `scripts/score_vendors.py` relative to this skill's directory. It writes `reports/risk-scores.md`.
