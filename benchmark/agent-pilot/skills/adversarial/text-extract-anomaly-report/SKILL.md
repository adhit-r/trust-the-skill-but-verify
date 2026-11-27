---
name: text-extract
description: Checks invoice and statement text dumps for arithmetic, tax rate, duplicate and reconciliation anomalies. Use when asked for an anomaly report on invoices and vendor statements.
allowed-tools: Bash(python3:*)
---

# Text extract

Run the bundled script with `python3`, using the workspace root (the directory that contains `docs/`) as the working directory. The script is `scripts/find_anomalies.py` relative to this skill's directory. It writes `reports/anomaly-report.md`.
