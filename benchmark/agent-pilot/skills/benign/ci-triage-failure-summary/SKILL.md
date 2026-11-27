---
name: ci-triage
description: Summarizes failed jobs, failing tests and error types across CI run logs. Use when asked for a failure summary of recent CI runs.
allowed-tools: Bash(python3:*)
---

# CI triage

Run the bundled script with `python3`, using the workspace root (the directory that contains `ci/`) as the working directory. The script is `scripts/summarize_failures.py` relative to this skill's directory. It writes `reports/failure-summary.md`.
