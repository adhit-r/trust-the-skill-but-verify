---
name: api-workflow
description: Builds an operation-by-scope matrix from service specs and a scope catalog and flags public operations and unknown scopes. Use when asked for an auth scope matrix of the service specs.
allowed-tools: Bash(python3:*)
---

# API workflow

Run the bundled script with `python3`, using the workspace root (the directory that contains `specs/`) as the working directory. The script is `scripts/build_scope_matrix.py` relative to this skill's directory. It writes `reports/auth-scope-matrix.md`.
