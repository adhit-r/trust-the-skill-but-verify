# Runtime Report Card

- Runtime profile: `RP2`
- Generated at: `1970-01-01T00:00:00+00:00`
- Boundary: Derived from existing contract findings, pairwise comparison artifacts, and trace events already present in the repository. Metrics that require benchmark-specific attack-success labels are represented conservatively with explicit proxy naming.

## Summary

| Runs | Benign | Adversarial | Unknown | Trace-valid | Pairwise comparisons | Expected pairwise comparisons |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 136 | 7 | 7 | 122 | 136 | 236 | 236 |

## Metrics

| Metric | Value | Numerator | Denominator |
| --- | ---: | ---: | ---: |
| Contract violation rate | 0.0956 | 13 | 136 |
| Attempted overreach rate | 0.0000 | 0 | 136 |
| Benign task success rate | 1.0000 | 7 | 7 |
| Secure benign success rate | 0.1429 | 1 | 7 |
| Adversarial realized-violation rate | 1.0000 | 7 | 7 |
| Utility cost rate | 0.0000 | 0 | 7 |
| Approval burden | 0.1429 | 1 | 7 |
| Runtime risk score proxy | 0.0449 | 122 | 2720 |

## Evidence Coverage

| Metric | Value | Numerator | Denominator |
| --- | ---: | ---: | ---: |
| Trace-valid rate | 1.0000 | 136 | 136 |
| Comparison-pair coverage rate | 1.0000 | 236 | 236 |
| Instrumentation-failure run rate | 0.0000 | 0 | 136 |

## Pairwise Disagreement

| Counterpart | Pairs | Runtime-drift candidate pairs | Mitigation/report-card pairs | Disagreements | Disagreement rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| `RP1` | 12 | 0 | 0 | 57 | 1.0000 |
| drift classes | D1 0.6667 | D2 0.5000 | D3 1.0000 | D4 1.0000 | D5 0.5000 |
| `RP3` | 136 | 8 | 0 | 39 | 0.0662 |
| drift classes | D1 0.0000 | D2 0.0368 | D3 0.0368 | D4 0.0368 | D5 0.0368 |
| `RP6` | 88 | 0 | 88 | 57 | 0.1477 |
| drift classes | D1 0.0000 | D2 0.0682 | D3 0.1477 | D4 0.0795 | D5 0.0682 |

## By Category

| Slice | Runs | Realized violations | Attempted overreach | Functional success | Attack-success proxy | Missing outputs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `api-workflow` | 17 | 0 | 0 | 17 | 0 | 0 |
| `compliance-audit` | 17 | 4 | 0 | 15 | 2 | 0 |
| `data-extraction` | 21 | 0 | 0 | 21 | 0 | 0 |
| `document-automation` | 23 | 4 | 0 | 22 | 2 | 0 |
| `local-file-operations` | 18 | 0 | 0 | 18 | 0 | 0 |
| `mcp-tool-workflow` | 16 | 1 | 0 | 16 | 1 | 0 |
| `network-egress` | 2 | 2 | 0 | 2 | 1 | 0 |
| `repository-maintenance` | 22 | 2 | 0 | 21 | 1 | 0 |

## By Attack Family

| Slice | Runs | Realized violations | Attempted overreach | Functional success | Attack-success proxy | Missing outputs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `benign` | 47 | 4 | 0 | 45 | 2 | 0 |
| `benign-or-canary-leak` | 2 | 2 | 0 | 1 | 1 | 0 |
| `benign-or-network-canary-leak` | 2 | 2 | 0 | 2 | 1 | 0 |
| `boundary-positive` | 39 | 0 | 0 | 39 | 0 | 0 |
| `negative-control` | 39 | 0 | 0 | 39 | 0 | 0 |
| `output-only` | 1 | 0 | 0 | 1 | 0 | 0 |
| `output-scope` | 4 | 4 | 0 | 3 | 2 | 0 |
| `restricted-tools` | 2 | 1 | 0 | 2 | 1 | 0 |
## Artifact Inputs

- Findings JSON files: `136`
- Comparison JSON files: `236`
