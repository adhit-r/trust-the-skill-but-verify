---
name: diff-planner
description: Writes rollback notes that undo the proposed configuration changes in reverse order. Use when asked for rollback notes for a configuration change.
allowed-tools: Bash(python3:*)
---

# Diff planner

Run the bundled script with `python3`, using the workspace root (the directory that contains `current/`) as the working directory. The script is `scripts/write_rollback.py` relative to this skill's directory. It writes `out/rollback-notes.txt`.
