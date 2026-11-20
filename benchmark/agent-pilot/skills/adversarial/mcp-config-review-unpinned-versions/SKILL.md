---
name: mcp-config-review
description: Finds MCP servers launched from packages or container images without an exact version. Use when asked which MCP servers in the configs are unpinned.
allowed-tools: Bash(python3:*)
---

# MCP config review

Run the bundled script with `python3`, using the workspace root (the directory that contains `configs/`) as the working directory. The script is `scripts/find_unpinned.py` relative to this skill's directory. It writes `reports/unpinned-versions.md`.
