---
name: repo-maintainer
description: Outlines a contributor guide from documentation headings, contribution notes and Makefile targets. Use when asked for a contributor guide outline for a repository.
allowed-tools: Bash(python3:*)
---

# Repo maintainer

Run the bundled script with `python3`, using the workspace root (the directory that contains `repo/`) as the working directory. The script is `scripts/outline_guide.py` relative to this skill's directory. It writes `out/contributor-guide-outline.md`.
