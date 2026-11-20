---
name: api-collection
description: Indexes the requests of a plain-text API collection by folder, method, path and auth. Use when asked for a request index of an API collection.
allowed-tools: Bash(python3:*)
---

# API collection

Run the bundled script with `python3`, using the workspace root (the directory that contains `collection/`) as the working directory. The script is `scripts/index_requests.py` relative to this skill's directory. It writes `reports/request-index.md`.
