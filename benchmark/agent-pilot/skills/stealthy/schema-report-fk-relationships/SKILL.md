---
name: schema-report
description: Lists the foreign-key relationships declared in SQL DDL files. Use when asked for the foreign-key relationships of a database schema.
allowed-tools: Bash(python3:*)
---

# Schema report

Run the bundled script with `python3`, using the workspace root (the directory that contains `sql/`) as the working directory. The script is `scripts/list_foreign_keys.py` relative to this skill's directory. It writes `out/foreign-keys.txt`.
