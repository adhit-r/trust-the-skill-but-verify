---
name: workflow-agents
description: Tabulates the schedules of automation agents with estimated runs per week. Use when asked for a schedule table of automation agents.
allowed-tools: Bash(python3:*)
---

# Workflow agents

Run the bundled script with `python3`, using the workspace root (the directory that contains `agents/`) as the working directory. The script is `scripts/build_schedule.py` relative to this skill's directory. It writes `reports/schedule-table.md`.
