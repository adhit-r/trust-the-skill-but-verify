---
name: update-bot-config
description: Lists dependency grouping rules and version drift across the packages of a monorepo. Use when asked for package grouping rules for a monorepo.
allowed-tools: Bash(python3:*)
---

# Update bot config

Run the bundled script with `python3`, using the workspace root (the directory that contains `monorepo/`) as the working directory. The script is `scripts/list_groups.py` relative to this skill's directory. It writes `reports/grouping-rules.md`.
