---
name: license-audit
description: Drafts a third-party NOTICE file from the copyright lines and licenses of vendored dependencies. Use when asked to draft a NOTICE file for the vendored dependencies of a project.
allowed-tools: Bash(python3:*)
---

# License audit

Run the bundled script with `python3`, using the workspace root (the directory that contains `project/`) as the working directory. The script is `scripts/build_notice.py` relative to this skill's directory. It writes `out/NOTICE.txt`.
