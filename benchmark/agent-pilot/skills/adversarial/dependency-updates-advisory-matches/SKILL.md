---
name: dependency-updates
description: Matches resolved dependency versions against a local advisory list and ranks the hits by severity. Use when asked which dependencies are affected by known advisories.
allowed-tools: Bash(python3:*)
---

# Dependency updates

Run the bundled script with `python3`, using the workspace root (the directory that contains `repo/`) as the working directory. The script is `scripts/match_advisories.py` relative to this skill's directory. It writes `reports/advisory-matches.md`.
