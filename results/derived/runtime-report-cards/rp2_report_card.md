# Runtime Report Card

- Runtime profile: `RP2`
- Generated at: `1970-01-01T00:00:00+00:00`
- Boundary: Derived from existing contract findings, pairwise comparison artifacts, and trace events already present in the repository. Metrics that require benchmark-specific attack-success labels are represented conservatively with explicit proxy naming.

## Summary

| Runs | Benign | Adversarial | Unknown | Trace-valid | Pairwise comparisons | Expected pairwise comparisons |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 7 | 7 | 50 | 64 | 90 | 90 |

## Metrics

| Metric | Value | Numerator | Denominator |
| --- | ---: | ---: | ---: |
| Contract violation rate | 0.1094 | 7 | 64 |
| Attempted overreach rate | 0.0000 | 0 | 64 |
| Benign task success rate | 1.0000 | 7 | 7 |
| Secure benign success rate | 1.0000 | 7 | 7 |
| Adversarial realized-violation rate | 1.0000 | 7 | 7 |
| Utility cost rate | 0.0000 | 0 | 7 |
| Approval burden | 0.1429 | 1 | 7 |
| Runtime risk score proxy | 0.0875 | 112 | 1280 |

## Evidence Coverage

| Metric | Value | Numerator | Denominator |
| --- | ---: | ---: | ---: |
| Trace-valid rate | 1.0000 | 64 | 64 |
| Comparison-pair coverage rate | 1.0000 | 90 | 90 |
| Instrumentation-failure run rate | 0.0000 | 0 | 64 |

## Pairwise Disagreement

| Counterpart | Pairs | Runtime-drift candidate pairs | Mitigation/report-card pairs | Disagreements | Disagreement rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| `RP1` | 12 | 0 | 0 | 37 | 1.0000 |
| drift classes | D1 0.0000 | D2 0.5000 | D3 0.0000 | D4 1.0000 | D5 0.5000 |
| `RP3` | 64 | 5 | 0 | 36 | 0.0938 |
| drift classes | D1 0.0000 | D2 0.0781 | D3 0.0156 | D4 0.0781 | D5 0.0781 |
| `RP6` | 14 | 0 | 14 | 53 | 0.7857 |
| drift classes | D1 0.5714 | D2 0.4286 | D3 0.0714 | D4 0.5000 | D5 0.4286 |

## By Category

| Slice | Runs | Realized violations | Attempted overreach | Functional success | Attack-success proxy | Missing outputs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `api-workflow` | 8 | 0 | 0 | 8 | 0 | 0 |
| `compliance-audit` | 11 | 2 | 0 | 9 | 2 | 0 |
| `data-extraction` | 9 | 0 | 0 | 9 | 0 | 0 |
| `document-automation` | 11 | 2 | 0 | 10 | 2 | 0 |
| `local-file-operations` | 6 | 0 | 0 | 6 | 0 | 0 |
| `mcp-tool-workflow` | 4 | 1 | 0 | 4 | 1 | 0 |
| `network-egress` | 2 | 1 | 0 | 2 | 1 | 0 |
| `repository-maintenance` | 13 | 1 | 0 | 12 | 1 | 0 |

## By Attack Family

| Slice | Runs | Realized violations | Attempted overreach | Functional success | Attack-success proxy | Missing outputs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `benign` | 23 | 2 | 0 | 21 | 2 | 0 |
| `benign-or-canary-leak` | 2 | 1 | 0 | 1 | 1 | 0 |
| `benign-or-network-canary-leak` | 2 | 1 | 0 | 2 | 1 | 0 |
| `boundary-positive` | 15 | 0 | 0 | 15 | 0 | 0 |
| `negative-control` | 15 | 0 | 0 | 15 | 0 | 0 |
| `output-only` | 1 | 0 | 0 | 1 | 0 | 0 |
| `output-scope` | 4 | 2 | 0 | 3 | 2 | 0 |
| `restricted-tools` | 2 | 1 | 0 | 2 | 1 | 0 |
## Artifact Inputs

- Findings JSON files: `64`
- Comparison JSON files: `90`
