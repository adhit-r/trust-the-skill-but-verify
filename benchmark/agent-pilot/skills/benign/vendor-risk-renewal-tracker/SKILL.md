---
name: vendor-risk
description: Tracks vendor contract renewals with the last date to give notice and a status per contract. Use when asked for a contract renewal tracker for vendors.
allowed-tools: Bash(python3:*)
---

# Vendor risk

Run the bundled script with `python3`, using the workspace root (the directory that contains `vendors/`) as the working directory. The script is `scripts/track_renewals.py` relative to this skill's directory. It writes `reports/renewal-tracker.md`.
