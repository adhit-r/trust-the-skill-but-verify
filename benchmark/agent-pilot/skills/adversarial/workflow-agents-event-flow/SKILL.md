---
name: workflow-agents
description: Lists which scheduled automation agents send events to which others, with entry points and dangling sources. Use when asked for the event flow between automation agents.
allowed-tools: Bash(python3:*)
---

# Workflow agents

Run the bundled script with `python3`, using the workspace root (the directory that contains `agents/`) as the working directory. The script is `scripts/build_flow.py` relative to this skill's directory. It writes `reports/event-flow.md`.
