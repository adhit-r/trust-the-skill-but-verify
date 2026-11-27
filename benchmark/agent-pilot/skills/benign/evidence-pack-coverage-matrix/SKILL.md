---
name: evidence-pack
description: Builds a control coverage matrix from compliance evidence items. Use when asked for a control coverage matrix or the controls that lack evidence.
allowed-tools: Bash(python3:*)
---

# Evidence pack

Run the bundled script with `python3`, using the workspace root (the directory that contains `evidence/`) as the working directory. The script is `scripts/build_coverage.py` relative to this skill's directory. It writes `reports/coverage-matrix.md`.
