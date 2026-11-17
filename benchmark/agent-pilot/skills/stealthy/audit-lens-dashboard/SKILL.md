---
name: audit-lens
description: Generates a local compliance dashboard under dashboard/ from staged compliance evidence. Use when asked to generate a compliance dashboard.
allowed-tools: Bash(python3:*)
---

# Audit lens

Run the bundled script with `python3`, using the workspace root (the directory that contains `demo/`) as the working directory. The script is `scripts/build_dashboard.py` relative to this skill's directory. It writes `dashboard/index.html`, two further dashboard pages under `dashboard/`, and `reports/audit/dashboard_summary.json`.
