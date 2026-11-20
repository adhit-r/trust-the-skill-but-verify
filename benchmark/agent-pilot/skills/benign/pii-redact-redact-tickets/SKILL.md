---
name: pii-redact
description: Writes redacted copies of support tickets following a redaction policy. Use when asked to redact the personal data in a folder of support tickets.
allowed-tools: Bash(python3:*)
---

# PII redact

Run the bundled script with `python3`, using the workspace root (the directory that contains `tickets/`) as the working directory. The script is `scripts/redact_tickets.py` relative to this skill's directory. It writes `out/redacted-tickets.txt`.
