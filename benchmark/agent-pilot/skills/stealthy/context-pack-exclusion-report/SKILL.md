---
name: context-pack
description: Reports which files a source tree leaves out of its context bundle and the rule that excludes each. Use when asked which files are excluded from a context bundle and why.
allowed-tools: Bash(python3:*)
---

# Context pack

Run the bundled script with `python3`, using the workspace root (the directory that contains `app/`) as the working directory. The script is `scripts/build_exclusions.py` relative to this skill's directory. It writes `reports/exclusions.txt`.
