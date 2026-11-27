---
name: diff-planner
description: Compares two versions of a service configuration directory and lists the changes to apply, file by file. Use when asked for a change plan between a current and a proposed configuration.
allowed-tools: Bash(python3:*)
---

# Diff planner

Run the bundled script with `python3`, using the workspace root (the directory that contains `current/`) as the working directory. The script is `scripts/plan_changes.py` relative to this skill's directory. It writes `reports/change-plan.md`.
