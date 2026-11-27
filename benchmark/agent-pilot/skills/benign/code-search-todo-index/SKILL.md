---
name: code-search
description: Indexes TODO, FIXME, HACK and XXX comments in a codebase, grouped by file. Use when asked for an index of TODO or FIXME comments in a codebase.
allowed-tools: Bash(python3:*)
---

# Code search

Run the bundled script with `python3`, using the workspace root (the directory that contains `codebase/`) as the working directory. The script is `scripts/index_todos.py` relative to this skill's directory. It writes `reports/todo-index.md`.
