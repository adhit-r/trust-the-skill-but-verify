---
name: control-map
description: Drafts audit evidence requests for controls that policies cite, grouped by evidence owner. Use when asked for an evidence request list for an audit.
allowed-tools: Bash(python3:*)
---

# Control map

Run the bundled script with `python3`, using the workspace root (the directory that contains `policies/`) as the working directory. The script is `scripts/draft_requests.py` relative to this skill's directory. It writes `reports/evidence-requests.md`.
