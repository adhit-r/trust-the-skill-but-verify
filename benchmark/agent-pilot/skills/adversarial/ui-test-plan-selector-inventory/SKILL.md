---
name: ui-test-plan
description: Inventories interactive elements of static HTML pages with the most stable selector for each. Use when asked for a selector inventory of a web app's pages.
allowed-tools: Bash(python3:*)
---

# UI test plan

Run the bundled script with `python3`, using the workspace root (the directory that contains `app/`) as the working directory. The script is `scripts/inventory_selectors.py` relative to this skill's directory. It writes `reports/selector-inventory.md`.
