---
name: patch-planner
description: Finds stale and merged branches in a branch export using the staleness window of the export. Use when asked for a stale branch report for a repository.
allowed-tools: Bash(python3:*)
---

# Patch planner

Run the bundled script with `python3`, using the workspace root (the directory that contains `repo/`) as the working directory. The script is `scripts/find_stale_branches.py` relative to this skill's directory. It writes `reports/stale-branches.md`.
