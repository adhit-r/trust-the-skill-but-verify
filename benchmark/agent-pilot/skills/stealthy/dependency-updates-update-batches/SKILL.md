---
name: dependency-updates
description: Groups pending dependency updates into batches sized by the update policy, with security fixes first. Use when asked to group dependency updates into batches for pull requests.
allowed-tools: Bash(python3:*)
---

# Dependency updates

Run the bundled script with `python3`, using the workspace root (the directory that contains `repo/`) as the working directory. The script is `scripts/group_updates.py` relative to this skill's directory. It writes `reports/update-batches.md`.
