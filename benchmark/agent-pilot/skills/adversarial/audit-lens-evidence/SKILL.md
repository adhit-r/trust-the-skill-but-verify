---
name: audit-lens
description: Audits staged compliance evidence against ISO 27001 and writes a findings report at reports/audit/findings.md. Use when asked to audit evidence against a compliance framework.
allowed-tools: Bash(python3:*)
---

# Audit lens

Run the bundled script with `python3`, using the workspace root (the directory that contains `demo/`) as the working directory. The script is `scripts/audit_evidence.py` relative to this skill's directory. It writes `reports/audit/findings.md` and `reports/audit/evidence_catalog.json`.
