---
name: ticket-summary
description: Reports tickets that missed their first-response or resolution SLA target using the exported ticket queues and the SLA policy. Use when asked for an SLA breach report on exported support tickets.
allowed-tools: Bash(python3:*)
---

# Ticket summary

Run the bundled script with `python3`, using the workspace root (the directory that contains `data/`) as the working directory. The script is `scripts/report_sla.py` relative to this skill's directory. It writes `reports/sla-breaches.md`.
