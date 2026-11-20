---
name: pii-redact
description: Logs where redactions apply in each support ticket by line number and type, with totals per queue. Use when asked for a redaction log for a folder of support tickets.
allowed-tools: Bash(python3:*)
---

# PII redact

Run the bundled script with `python3`, using the workspace root (the directory that contains `tickets/`) as the working directory. The script is `scripts/write_redaction_log.py` relative to this skill's directory. It writes `reports/redaction-log.md`.
