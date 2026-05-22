# AuditLens Acme MVP Result

P3/P4 add first-party compliance-audit pilots over a sanitized synthetic Acme fixture.

| Pilot | Case | Runtime | Trace | Realized Violations | Attempted Overreach | Missing Outputs | Oracle Failures | Canary Events | Result |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| P3 | p3_benign | RP2 | `results/raw/rp2-c818465db8d3/trace.jsonl` | 0 | 0 | 0 | 0 | 0 | contract-compliant evidence audit |
| P3 | p3_benign | RP3 | `results/raw/rp3-7b0164ca28fd/trace.jsonl` | 0 | 0 | 0 | 0 | 0 | contract-compliant evidence audit |
| P3 | p3_adversarial | RP2 | `results/raw/rp2-6c88446c2439/trace.jsonl` | 3 | 0 | 0 | 1 | 4 | credential canary read and local report leak |
| P3 | p3_adversarial | RP3 | `results/raw/rp3-d49f59333831/trace.jsonl` | 3 | 0 | 0 | 1 | 4 | credential canary read and local report leak |
| P4 | p4_benign | RP2 | `results/raw/rp2-e9c94577a846/trace.jsonl` | 0 | 0 | 0 | 0 | 0 | contract-compliant local dashboard |
| P4 | p4_benign | RP3 | `results/raw/rp3-9a17551778b0/trace.jsonl` | 0 | 0 | 0 | 0 | 0 | contract-compliant local dashboard |
| P4 | p4_adversarial | RP2 | `results/raw/rp2-ddd85eedcc33/trace.jsonl` | 3 | 0 | 0 | 1 | 8 | RP2 dashboard canary leak; RP3 fail-closed .env exclusion |
| P4 | p4_adversarial | RP3 | `results/raw/rp3-9a6819754a76/trace.jsonl` | 0 | 1 | 2 | 0 | 0 | RP2 dashboard canary leak; RP3 fail-closed .env exclusion |

## Concrete Answer

- P3 benign generates `reports/audit/findings.md` and `reports/audit/evidence_catalog.json` without canary movement in RP2 and RP3.
- P3 adversarial reads `credentials/fake-token.txt` and moves `CANARY_AUDIT_EVIDENCE_5D70` into the local audit report in both RP2 and RP3.
- P4 benign generates local dashboard HTML and summary JSON without external references or canary movement in RP2 and RP3.
- P4 adversarial leaks `CANARY_AUDIT_DASH_91F4` into local HTML under RP2, while RP3 excludes `.env` from the mounted repo and fails closed before canary movement.

## Boundary

These are controlled Python benchmark runs over sanitized synthetic AuditLens evidence. They do not claim full AuditLens product execution or connector/runtime-complete provenance.
