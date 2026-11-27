---
name: audit-pack
description: Builds an audit pack index linking controls to their test notes and mapped evidence exports. Use when asked for an audit pack index of controls and evidence.
allowed-tools: Bash(python3:*)
---

# Audit pack

Run the bundled script with `python3`, using the workspace root (the directory that contains `evidence/`) as the working directory. The script is `scripts/build_index.py` relative to this skill's directory. It writes `out/evidence-index.md`.
