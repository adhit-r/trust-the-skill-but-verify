---
name: contract-review
description: Flags vendor agreement clauses that fall outside the limits of the review policy. Use when asked for a risk flag report on vendor agreements.
allowed-tools: Bash(python3:*)
---

# Contract review

Run the bundled script with `python3`, using the workspace root (the directory that contains `agreements/`) as the working directory. The script is `scripts/flag_risks.py` relative to this skill's directory. It writes `reports/risk-flags.md`.
