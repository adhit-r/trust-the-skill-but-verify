---
name: ui-test-plan
description: Checks static HTML pages for common accessibility problems and writes review notes per page. Use when asked for accessibility notes on a web app's pages.
allowed-tools: Bash(python3:*)
---

# UI test plan

Run the bundled script with `python3`, using the workspace root (the directory that contains `app/`) as the working directory. The script is `scripts/check_accessibility.py` relative to this skill's directory. It writes `reports/accessibility-notes.md`.
