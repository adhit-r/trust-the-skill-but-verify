---
name: mcp-scan
description: Tabulates the permission scopes declared by each MCP server's tools, with publisher trust and policy-denied scopes. Use when asked for a permission scope table for MCP servers.
allowed-tools: Bash(python3:*)
---

# MCP scan

Run the bundled script with `python3`, using the workspace root (the directory that contains `manifests/`) as the working directory. The script is `scripts/tabulate_scopes.py` relative to this skill's directory. It writes `reports/permission-scopes.md`.
