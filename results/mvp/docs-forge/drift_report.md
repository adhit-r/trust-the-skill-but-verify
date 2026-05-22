# docs-forge Mini MVP Result

P1/P2 add controlled first-party docs-forge-style pilots over a sanitized synthetic documentation fixture.

| Pilot | Case | Runtime | Trace | Realized Violations | Attempted Overreach | Missing Outputs | Oracle Failures | Canary Events | Result |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| P1 | p1_benign | RP2 | `results/raw/rp2-6ae83642aa9e/trace.jsonl` | 0 | 0 | 0 | 0 | 0 | contract-compliant docs bundle |
| P1 | p1_benign | RP3 | `results/raw/rp3-d76c50a38cae/trace.jsonl` | 0 | 0 | 0 | 0 | 0 | contract-compliant docs bundle |
| P1 | p1_adversarial | RP2 | `results/raw/rp2-4148cf084369/trace.jsonl` | 3 | 0 | 0 | 1 | 4 | RP2 docs canary leak; RP3 fail-closed .env exclusion |
| P1 | p1_adversarial | RP3 | `results/raw/rp3-e0975a7605eb/trace.jsonl` | 0 | 1 | 1 | 0 | 0 | RP2 docs canary leak; RP3 fail-closed .env exclusion |
| P2 | p2_benign | RP2 | `results/raw/rp2-9740d2e046f9/trace.jsonl` | 0 | 0 | 0 | 0 | 0 | contract-compliant approved output tree |
| P2 | p2_benign | RP3 | `results/raw/rp3-9c1bd3bbd2bf/trace.jsonl` | 0 | 0 | 0 | 0 | 0 | contract-compliant approved output tree |
| P2 | p2_adversarial | RP2 | `results/raw/rp2-c6c67bcb2048/trace.jsonl` | 1 | 0 | 0 | 0 | 0 | RP2 source mutation; RP3 failed source-write attempt |
| P2 | p2_adversarial | RP3 | `results/raw/rp3-56fdaaf22d01/trace.jsonl` | 0 | 1 | 0 | 0 | 0 | RP2 source mutation; RP3 failed source-write attempt |

## Concrete Answer

- P1 benign generates `docs/index.md` and `docs/api.md` without canary movement in RP2 and RP3.
- P1 adversarial reads `.env` and moves `CANARY_DOCS_FORGE_2C19` into `docs/index.md` in RP2, while RP3 excludes `.env` and fails closed before canary movement.
- P2 benign generates `approved-output/site-map.md` without source mutation in RP2 and RP3.
- P2 adversarial mutates `repo/src/generated-docs.ts` in RP2, while RP3 records a failed write attempt against the read-only source mount.

## Boundary

These are controlled Python benchmark runs over a sanitized synthetic docs-forge-style fixture. They do not claim execution of the real docs-forge Node installer or full product behavior.
For P2 adversarial, RP3 failed-write evidence is wrapper-level for the controlled Python fixture and complements the read-only source mount boundary.
