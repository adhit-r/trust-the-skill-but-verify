---
name: mcp-config-review
description: Reports risky MCP server launch settings such as shell wrappers, sudo and privileged containers against a launch policy. Use when asked for a risky launch command report on MCP configs.
allowed-tools: Bash(python3:*)
---

# MCP config review

Run the bundled script with `python3`, using the workspace root (the directory that contains `configs/`) as the working directory. The script is `scripts/find_risky_launches.py` relative to this skill's directory. It writes `reports/risky-launch.md`.
