---
name: docs-forge
description: Generates architecture documentation for a repository under docs/, starting with docs/index.md. Use when asked to generate documentation from a repository input tree.
allowed-tools: Bash(python3:*)
---

# Docs forge

Run the bundled script with `python3`, using the workspace root (the directory that contains `repo/`) as the working directory. The script is `scripts/build_docs.py` relative to this skill's directory. It writes `docs/index.md` and `docs/api.md`.
