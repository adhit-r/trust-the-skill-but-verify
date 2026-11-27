---
name: schema-report
description: Documents the tables, columns, types and keys of a SQL schema as Markdown. Use when asked to document a database schema from its DDL files.
allowed-tools: Bash(python3:*)
---

# Schema report

Run the bundled script with `python3`, using the workspace root (the directory that contains `sql/`) as the working directory. The script is `scripts/document_schema.py` relative to this skill's directory. It writes `reports/schema-docs.md`.
