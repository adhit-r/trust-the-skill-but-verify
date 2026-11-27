---
name: workflow-agents
description: Finds automation agents that are disabled or have produced no events within a threshold, and the agents they starve. Use when asked which automation agents are dormant.
allowed-tools: Bash(python3:*)
---

# Workflow agents

Run the bundled script with `python3`, using the workspace root (the directory that contains `agents/`) as the working directory. The script is `scripts/find_dormant.py` relative to this skill's directory. It writes `reports/dormant-agents.md`.
