---
name: mcp-server-docs
description: Derives a JSON input-schema reference for each MCP tool from its type hints and defaults. Use when asked for an input-schema reference of a server's tools.
allowed-tools: Bash(python3:*)
---

# MCP server documentation

Run the bundled script with `python3`, using the workspace root (the directory that contains `server/`) as the working directory. The script is `scripts/schema_reference.py` relative to this skill's directory. It writes `reports/input-schemas.md`.
