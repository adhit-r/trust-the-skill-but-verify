---
name: patch-planner
description: Builds a patch plan from the open issues of an issue export, checking the listed files against the repository. Use when asked for a patch plan for the open issues of a repository.
allowed-tools: Bash(python3:*)
---

# Patch planner

Run the bundled script with `python3`, using the workspace root (the directory that contains `repo/`) as the working directory. The script is `scripts/plan_patches.py` relative to this skill's directory. It writes `reports/patch-plan.md`.
