---
name: audit-pack
description: Tabulates control test notes into a results table with exception rates and consistency checks. Use when asked for a control test results table from test notes.
allowed-tools: Bash(python3:*)
---

# Audit pack

Run the bundled script with `python3`, using the workspace root (the directory that contains `evidence/`) as the working directory. The script is `scripts/build_results.py` relative to this skill's directory. It writes `reports/control-test-results.md`.
