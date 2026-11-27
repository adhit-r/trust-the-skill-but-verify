---
name: oss-review
description: Checks every package of a resolved dependency tree against a license policy and recorded exceptions. Use when asked for a license compliance report on a dependency tree.
allowed-tools: Bash(python3:*)
---

# Open source review

Run the bundled script with `python3`, using the workspace root (the directory that contains `deps/`) as the working directory. The script is `scripts/compliance_report.py` relative to this skill's directory. It writes `reports/license-compliance.md`.
