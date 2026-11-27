---
name: mcp-scan
description: Proposes an allow, review or deny decision for every MCP tool from the allowlist policy and publisher trust. Use when asked for an allowlist proposal for MCP tools.
allowed-tools: Bash(python3:*)
---

# MCP scan

Run the bundled script with `python3`, using the workspace root (the directory that contains `manifests/`) as the working directory. The script is `scripts/propose_allowlist.py` relative to this skill's directory. It writes `out/allowlist-proposal.json`.
