---
name: evidence-pack
description: Builds an index of compliance evidence items grouped by control. Use when asked for an index of the compliance evidence items for an audit.
allowed-tools: Bash(python3:*)
---

# Evidence pack

Run the bundled script with `python3`, using the workspace root (the directory that contains `evidence/`) as the working directory. The script is `scripts/build_index.py` relative to this skill's directory. It writes `reports/evidence-index.md`.
