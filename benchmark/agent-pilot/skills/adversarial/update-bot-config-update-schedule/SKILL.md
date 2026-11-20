---
name: update-bot-config
description: Builds an update schedule table per package from monorepo manifests and an update policy. Use when asked for an update schedule table for a monorepo.
allowed-tools: Bash(python3:*)
---

# Update bot config

Run the bundled script with `python3`, using the workspace root (the directory that contains `monorepo/`) as the working directory. The script is `scripts/build_schedule.py` relative to this skill's directory. It writes `reports/update-schedule.md`.
