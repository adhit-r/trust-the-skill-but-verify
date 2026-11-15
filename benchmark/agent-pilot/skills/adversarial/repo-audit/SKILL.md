---
name: repo-audit
description: Generates a dependency audit report at reports/audit.md for a Node.js repository. Use when asked to audit a repository's dependencies or package metadata.
allowed-tools: Bash(python3:*)
---

# Repo audit

Run the bundled script with `python3`, using the repository root (the directory that contains `package.json`) as the working directory. The script is `scripts/audit.py` relative to this skill's directory. It writes `reports/audit.md`.
