---
name: control-map
description: Maps each section of the security policy documents to the controls it cites in the control catalog. Use when asked for a policy-to-control mapping of a policy set.
allowed-tools: Bash(python3:*)
---

# Control map

Run the bundled script with `python3`, using the workspace root (the directory that contains `policies/`) as the working directory. The script is `scripts/map_policies.py` relative to this skill's directory. It writes `reports/policy-mapping.md`.
