---
name: mcp-scan
description: Scans tool descriptions in MCP server manifests for risky wording patterns such as credential paths, silent actions and external URLs. Use when asked for a description pattern report on MCP tool manifests.
allowed-tools: Bash(python3:*)
---

# MCP scan

Run the bundled script with `python3`, using the workspace root (the directory that contains `manifests/`) as the working directory. The script is `scripts/scan_patterns.py` relative to this skill's directory. It writes `reports/pattern-report.md`.
