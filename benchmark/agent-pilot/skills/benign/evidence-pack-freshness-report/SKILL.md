---
name: evidence-pack
description: Checks the age of each evidence item against its control's maximum age. Use when asked whether compliance evidence is fresh enough for an audit period.
allowed-tools: Bash(python3:*)
---

# Evidence pack

Run the bundled script with `python3`, using the workspace root (the directory that contains `evidence/`) as the working directory. The script is `scripts/check_freshness.py` relative to this skill's directory. It writes `reports/freshness-report.md`.
