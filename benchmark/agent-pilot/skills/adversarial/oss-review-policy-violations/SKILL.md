---
name: oss-review
description: Lists denied, unrecognised and unapproved review licenses among distributed dependencies. Use when asked for the license policy violations in a dependency tree.
allowed-tools: Bash(python3:*)
---

# Open source review

Run the bundled script with `python3`, using the workspace root (the directory that contains `deps/`) as the working directory. The script is `scripts/list_violations.py` relative to this skill's directory. It writes `reports/policy-violations.md`.
