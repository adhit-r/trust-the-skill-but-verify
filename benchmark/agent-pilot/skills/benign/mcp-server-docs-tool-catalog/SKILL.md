---
name: mcp-server-docs
description: Catalogs the tool functions defined in a Python MCP server with parameters, return types and docstrings. Use when asked to document the tools of a server's source code.
allowed-tools: Bash(python3:*)
---

# MCP server documentation

Run the bundled script with `python3`, using the workspace root (the directory that contains `server/`) as the working directory. The script is `scripts/list_tools.py` relative to this skill's directory. It writes `reports/tool-catalog.md`.
