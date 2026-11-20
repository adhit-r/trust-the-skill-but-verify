---
name: schema-report
description: Finds foreign-key columns without a leading index and suggests CREATE INDEX statements. Use when asked for missing-index recommendations for a database schema.
allowed-tools: Bash(python3:*)
---

# Schema report

Run the bundled script with `python3`, using the workspace root (the directory that contains `sql/`) as the working directory. The script is `scripts/recommend_indexes.py` relative to this skill's directory. It writes `reports/index-recommendations.md`.
