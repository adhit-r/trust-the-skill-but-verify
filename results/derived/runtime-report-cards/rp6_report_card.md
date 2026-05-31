# Runtime Report Card

- Runtime profile: `RP6`
- Generated at: `1970-01-01T00:00:00+00:00`
- Boundary: Derived from existing contract findings, pairwise comparison artifacts, and trace events already present in the repository. Metrics that require benchmark-specific attack-success labels are represented conservatively with explicit proxy naming.

## Summary

| Runs | Benign | Adversarial | Unknown | Trace-valid | Pairwise comparisons | Expected pairwise comparisons |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 89 | 7 | 7 | 75 | 89 | 176 | 188 |

## Metrics

| Metric | Value | Numerator | Denominator |
| --- | ---: | ---: | ---: |
| Contract violation rate | 0.0000 | 0 | 89 |
| Attempted overreach rate | 0.0899 | 8 | 89 |
| Benign task success rate | 1.0000 | 7 | 7 |
| Secure benign success rate | 1.0000 | 7 | 7 |
| Adversarial realized-violation rate | 0.0000 | 0 | 7 |
| Utility cost rate | 0.0000 | 0 | 7 |
| Approval burden | 1.0000 | 7 | 7 |
| Runtime risk score proxy | 0.0000 | 0 | 1780 |

## Evidence Coverage

| Metric | Value | Numerator | Denominator |
| --- | ---: | ---: | ---: |
| Trace-valid rate | 1.0000 | 89 | 89 |
| Comparison-pair coverage rate | 0.9362 | 176 | 188 |
| Instrumentation-failure run rate | 0.0000 | 0 | 89 |

## Pairwise Disagreement

| Counterpart | Pairs | Runtime-drift candidate pairs | Mitigation/report-card pairs | Disagreements | Disagreement rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| `RP2` | 88 | 0 | 88 | 53 | 0.1250 |
| drift classes | D1 0.0909 | D2 0.0682 | D3 0.0114 | D4 0.0795 | D5 0.0682 |
| `RP3` | 88 | 0 | 88 | 21 | 0.1136 |
| drift classes | D1 0.0909 | D2 0.0227 | D3 0.0000 | D4 0.0341 | D5 0.0227 |

## By Category

| Slice | Runs | Realized violations | Attempted overreach | Functional success | Attack-success proxy | Missing outputs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `api-workflow` | 9 | 0 | 0 | 9 | 0 | 0 |
| `compliance-audit` | 11 | 0 | 2 | 9 | 0 | 2 |
| `data-extraction` | 12 | 0 | 0 | 12 | 0 | 0 |
| `document-automation` | 17 | 0 | 2 | 16 | 0 | 1 |
| `local-file-operations` | 12 | 0 | 0 | 12 | 0 | 0 |
| `mcp-tool-workflow` | 14 | 0 | 1 | 14 | 0 | 0 |
| `network-egress` | 3 | 0 | 2 | 2 | 0 | 1 |
| `repository-maintenance` | 11 | 0 | 1 | 10 | 0 | 1 |

## By Attack Family

| Slice | Runs | Realized violations | Attempted overreach | Functional success | Attack-success proxy | Missing outputs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `benign` | 29 | 0 | 2 | 27 | 0 | 2 |
| `benign-or-canary-leak` | 2 | 0 | 1 | 1 | 0 | 1 |
| `benign-or-network-canary-leak` | 3 | 0 | 2 | 2 | 0 | 1 |
| `boundary-positive` | 24 | 0 | 0 | 24 | 0 | 0 |
| `negative-control` | 25 | 0 | 0 | 25 | 0 | 0 |
| `output-scope` | 4 | 0 | 2 | 3 | 0 | 1 |
| `restricted-tools` | 2 | 0 | 1 | 2 | 0 | 0 |
## Artifact Inputs

- Findings JSON files: `89`
- Comparison JSON files: `88`
