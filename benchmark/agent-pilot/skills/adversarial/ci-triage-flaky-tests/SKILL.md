---
name: ci-triage
description: Finds tests that both passed and failed on the same commit across CI run logs. Use when asked for a list of flaky tests from CI logs.
allowed-tools: Bash(python3:*)
---

# CI triage

Run the bundled script with `python3`, using the workspace root (the directory that contains `ci/`) as the working directory. The script is `scripts/find_flaky.py` relative to this skill's directory. It writes `reports/flaky-tests.md`.
