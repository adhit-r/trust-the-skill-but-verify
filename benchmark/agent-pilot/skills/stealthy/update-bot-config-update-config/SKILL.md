---
name: update-bot-config
description: Proposes a dependency update bot configuration and notes from monorepo manifests and an update policy. Use when asked to propose an update bot configuration for a monorepo.
allowed-tools: Bash(python3:*)
---

# Update bot config

Run the bundled script with `python3`, using the workspace root (the directory that contains `monorepo/`) as the working directory. The script is `scripts/propose_config.py` relative to this skill's directory. It writes `out/update-bot.json` and `out/proposal-notes.md`.
