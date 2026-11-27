---
name: patch-planner
description: Drafts release notes from conventional commit subjects since the last release and proposes the next version. Use when asked to draft release notes for the next version of a repository.
allowed-tools: Bash(python3:*)
---

# Patch planner

Run the bundled script with `python3`, using the workspace root (the directory that contains `repo/`) as the working directory. The script is `scripts/draft_release_notes.py` relative to this skill's directory. It writes `out/RELEASE_NOTES.md`.
