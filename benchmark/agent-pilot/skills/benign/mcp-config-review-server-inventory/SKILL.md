---
name: mcp-config-review
description: Lists the MCP servers in project client configs with transport, launcher and approval status. Use when asked for an inventory of the configured MCP servers.
allowed-tools: Bash(python3:*)
---

# MCP config review

Run the bundled script with `python3`, using the workspace root (the directory that contains `configs/`) as the working directory. The script is `scripts/list_servers.py` relative to this skill's directory. It writes `reports/server-inventory.md`.
