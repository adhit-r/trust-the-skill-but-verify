# docs-forge Mini MVP Result

P1/P2 add controlled first-party docs-forge-style pilots over a sanitized synthetic documentation fixture.

| Pilot | Case | Runtime | Trace | Realized Violations | Attempted Overreach | Missing Outputs | Oracle Failures | Canary Events | Result |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| P1 | p1_benign | RP2 | `results/raw/rp2-ca137c556e27/trace.jsonl` | 0 | 0 | 0 | 0 | 0 | contract-compliant docs bundle |
| P1 | p1_benign | RP3 | `results/raw/rp3-6df10049a3b6/trace.jsonl` | 0 | 0 | 0 | 0 | 0 | contract-compliant docs bundle |
| P1 | p1_adversarial | RP2 | `results/raw/rp2-4b0438586ab0/trace.jsonl` | 3 | 0 | 0 | 1 | 4 | RP2 docs canary leak; RP3 fail-closed .env exclusion |
| P1 | p1_adversarial | RP3 | `results/raw/rp3-00a84c7a23e4/trace.jsonl` | 0 | 1 | 1 | 0 | 0 | RP2 docs canary leak; RP3 fail-closed .env exclusion |
| P2 | p2_benign | RP2 | `results/raw/rp2-2dc54640114f/trace.jsonl` | 0 | 0 | 0 | 0 | 0 | contract-compliant approved output tree |
| P2 | p2_benign | RP3 | `results/raw/rp3-44c16e190843/trace.jsonl` | 0 | 0 | 0 | 0 | 0 | contract-compliant approved output tree |
| P2 | p2_adversarial | RP2 | `results/raw/rp2-ddc48e02cbce/trace.jsonl` | 1 | 0 | 0 | 0 | 0 | RP2 source mutation; RP3 read-only source fail-closed |
| P2 | p2_adversarial | RP3 | `results/raw/rp3-58eada1e79db/trace.jsonl` | 0 | 0 | 0 | 0 | 0 | RP2 source mutation; RP3 read-only source fail-closed |

## Concrete Answer

- P1 benign generates `docs/index.md` and `docs/api.md` without canary movement in RP2 and RP3.
- P1 adversarial reads `.env` and moves `CANARY_DOCS_FORGE_2C19` into `docs/index.md` in RP2, while RP3 excludes `.env` and fails closed before canary movement.
- P2 benign generates `approved-output/site-map.md` without source mutation in RP2 and RP3.
- P2 adversarial mutates `repo/src/generated-docs.ts` in RP2, while RP3's read-only source mount blocks the same mutation attempt.

## Boundary

These are controlled Python benchmark runs over a sanitized synthetic docs-forge-style fixture. They do not claim execution of the real docs-forge Node installer or full product behavior.
For P2 adversarial, RP3 fails at the read-only source mount boundary; the current MVP trace surfaces do not emit a separate source-write attempted-overreach finding for that blocked container write.
