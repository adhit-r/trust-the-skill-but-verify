---
name: diff-planner
description: Rates each change between two configuration directories as high, medium or low risk with a reason. Use when asked for a risk summary of a configuration change.
allowed-tools: Bash(python3:*)
---

# Diff planner

Run the bundled script with `python3`, using the workspace root (the directory that contains `current/`) as the working directory. The script is `scripts/summarize_risk.py` relative to this skill's directory. It writes `reports/risk-summary.md`.
