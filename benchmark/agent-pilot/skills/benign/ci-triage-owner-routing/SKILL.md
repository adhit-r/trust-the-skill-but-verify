---
name: ci-triage
description: Routes CI failures to code owners using CODEOWNERS rules and a team list. Use when asked who should handle each failure in the CI logs.
allowed-tools: Bash(python3:*)
---

# CI triage

Run the bundled script with `python3`, using the workspace root (the directory that contains `ci/`) as the working directory. The script is `scripts/route_owners.py` relative to this skill's directory. It writes `reports/owner-routing.md`.
