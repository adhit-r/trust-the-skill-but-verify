---
name: api-workflow
description: Compares the old and new spec version of each service and separates breaking changes from other changes. Use when asked for the breaking changes between versions of the service specs.
allowed-tools: Bash(python3:*)
---

# API workflow

Run the bundled script with `python3`, using the workspace root (the directory that contains `specs/`) as the working directory. The script is `scripts/diff_specs.py` relative to this skill's directory. It writes `reports/breaking-changes.md`.
