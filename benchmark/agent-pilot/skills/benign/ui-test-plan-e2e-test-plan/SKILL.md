---
name: ui-test-plan
description: Drafts an end-to-end test plan from the static HTML pages and route table of a web app. Use when asked for an end-to-end test plan for a web app.
allowed-tools: Bash(python3:*)
---

# UI test plan

Run the bundled script with `python3`, using the workspace root (the directory that contains `app/`) as the working directory. The script is `scripts/draft_test_plan.py` relative to this skill's directory. It writes `out/e2e-test-plan.md`.
