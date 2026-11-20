---
name: api-workflow
description: Lists the endpoints of the current internal service specs with their auth requirement and owning team. Use when asked for an endpoint inventory of the service specs.
allowed-tools: Bash(python3:*)
---

# API workflow

Run the bundled script with `python3`, using the workspace root (the directory that contains `specs/`) as the working directory. The script is `scripts/list_endpoints.py` relative to this skill's directory. It writes `reports/endpoint-inventory.md`.
