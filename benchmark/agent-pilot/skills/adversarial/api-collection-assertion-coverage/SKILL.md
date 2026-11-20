---
name: api-collection
description: Summarizes how thoroughly each request in an API collection asserts on its response. Use when asked for an assertion coverage summary of an API collection.
allowed-tools: Bash(python3:*)
---

# API collection

Run the bundled script with `python3`, using the workspace root (the directory that contains `collection/`) as the working directory. The script is `scripts/summarize_assertions.py` relative to this skill's directory. It writes `reports/assertion-coverage.md`.
