---
name: code-search
description: Counts occurrences of configured search strings per file in a codebase. Use when asked for occurrence counts of tracked strings in a codebase.
allowed-tools: Bash(python3:*)
---

# Code search

Run the bundled script with `python3`, using the workspace root (the directory that contains `codebase/`) as the working directory. The script is `scripts/count_strings.py` relative to this skill's directory. It writes `reports/string-occurrences.md`.
