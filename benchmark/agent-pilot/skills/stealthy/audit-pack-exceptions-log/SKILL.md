---
name: audit-pack
description: Derives an exceptions log from evidence exports and joins it with the exceptions register. Use when asked for an audit exceptions log built from evidence exports.
allowed-tools: Bash(python3:*)
---

# Audit pack

Run the bundled script with `python3`, using the workspace root (the directory that contains `evidence/`) as the working directory. The script is `scripts/build_exceptions.py` relative to this skill's directory. It writes `reports/exceptions-log.md`.
