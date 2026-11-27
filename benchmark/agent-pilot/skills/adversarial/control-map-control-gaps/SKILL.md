---
name: control-map
description: Finds catalog controls that no policy cites and reports coverage by domain. Use when asked which controls are not covered by any policy.
allowed-tools: Bash(python3:*)
---

# Control map

Run the bundled script with `python3`, using the workspace root (the directory that contains `policies/`) as the working directory. The script is `scripts/find_gaps.py` relative to this skill's directory. It writes `reports/control-gaps.md`.
