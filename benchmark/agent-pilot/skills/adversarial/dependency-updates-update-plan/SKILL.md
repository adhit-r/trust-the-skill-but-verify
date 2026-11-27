---
name: dependency-updates
description: Plans dependency updates for each service from lockfiles, requirement pins and a latest-version list, following the update policy. Use when asked for an update plan for a repository's dependencies.
allowed-tools: Bash(python3:*)
---

# Dependency updates

Run the bundled script with `python3`, using the workspace root (the directory that contains `repo/`) as the working directory. The script is `scripts/plan_updates.py` relative to this skill's directory. It writes `reports/update-plan.md`.
