---
name: repo-maintainer
description: Collects TODO and FIXME comments from source and test files into a report. Use when asked for a TODO or FIXME report on a repository.
allowed-tools: Bash(python3:*)
---

# Repo maintainer

Run the bundled script with `python3`, using the workspace root (the directory that contains `repo/`) as the working directory. The script is `scripts/report_todos.py` relative to this skill's directory. It writes `reports/todo-report.md`.
