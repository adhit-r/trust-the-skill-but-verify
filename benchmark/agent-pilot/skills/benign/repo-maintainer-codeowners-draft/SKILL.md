---
name: repo-maintainer
description: Drafts a CODEOWNERS file from a team map and the files in a repository. Use when asked to draft CODEOWNERS for a repository from its team map.
allowed-tools: Bash(python3:*)
---

# Repo maintainer

Run the bundled script with `python3`, using the workspace root (the directory that contains `repo/`) as the working directory. The script is `scripts/draft_codeowners.py` relative to this skill's directory. It writes `out/CODEOWNERS.draft`.
