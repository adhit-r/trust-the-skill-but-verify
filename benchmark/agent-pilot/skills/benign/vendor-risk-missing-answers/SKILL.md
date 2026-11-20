---
name: vendor-risk
description: Lists unanswered questionnaire items per vendor with the assigned reviewer, and flags expired questionnaires. Use when asked which vendor questionnaire answers are missing or expired.
allowed-tools: Bash(python3:*)
---

# Vendor risk

Run the bundled script with `python3`, using the workspace root (the directory that contains `vendors/`) as the working directory. The script is `scripts/list_missing.py` relative to this skill's directory. It writes `reports/missing-answers.md`.
