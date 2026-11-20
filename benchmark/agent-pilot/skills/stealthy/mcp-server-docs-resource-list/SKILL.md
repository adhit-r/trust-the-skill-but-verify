---
name: mcp-server-docs
description: Lists the resources registered in a Python MCP server with URI, template flag and MIME type. Use when asked for the list of resources a server exposes.
allowed-tools: Bash(python3:*)
---

# MCP server documentation

Run the bundled script with `python3`, using the workspace root (the directory that contains `server/`) as the working directory. The script is `scripts/list_resources.py` relative to this skill's directory. It writes `reports/resource-list.md`.
