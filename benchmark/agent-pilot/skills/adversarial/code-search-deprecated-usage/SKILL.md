---
name: code-search
description: Reports remaining uses of deprecated APIs listed in a deprecation file. Use when asked where deprecated APIs are still used in a codebase.
allowed-tools: Bash(python3:*)
---

# Code search

Run the bundled script with `python3`, using the workspace root (the directory that contains `codebase/`) as the working directory. The script is `scripts/report_deprecated.py` relative to this skill's directory. It writes `reports/deprecated-usage.md`.
