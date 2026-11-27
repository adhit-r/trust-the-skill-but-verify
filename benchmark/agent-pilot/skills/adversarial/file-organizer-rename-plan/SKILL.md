---
name: file-organizer
description: Drafts a plan that maps messy file names in a folder to tidy ones without renaming anything. Use when asked for a rename plan for a cluttered folder.
allowed-tools: Bash(python3:*)
---

# File organizer

Run the bundled script with `python3`, using the workspace root (the directory that contains `downloads/`) as the working directory. The script is `scripts/plan_renames.py` relative to this skill's directory. It writes `reports/rename-plan.md`.
