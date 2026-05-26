# Runtime Report Card

- Runtime profile: `RP6`
- Generated at: `1970-01-01T00:00:00+00:00`
- Boundary: Derived from existing contract findings, pairwise comparison artifacts, and trace events already present in the repository. Metrics that require benchmark-specific attack-success labels are represented conservatively with explicit proxy naming.

## Summary

| Runs | Benign | Adversarial | Unknown | Trace-valid | Pairwise comparisons | Expected pairwise comparisons |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 15 | 7 | 7 | 1 | 15 | 28 | 40 |

## Metrics

| Metric | Value | Numerator | Denominator |
| --- | ---: | ---: | ---: |
| Contract violation rate | 0.0000 | 0 | 15 |
| Attempted overreach rate | 0.5333 | 8 | 15 |
| Benign task success rate | 1.0000 | 7 | 7 |
| Secure benign success rate | 1.0000 | 7 | 7 |
| Adversarial realized-violation rate | 0.0000 | 0 | 7 |
| Utility cost rate | 0.0000 | 0 | 7 |
| Approval burden | 1.0000 | 7 | 7 |
| Runtime risk score proxy | 0.0000 | 0 | 300 |

## Evidence Coverage

| Metric | Value | Numerator | Denominator |
| --- | ---: | ---: | ---: |
| Trace-valid rate | 1.0000 | 15 | 15 |
| Comparison-pair coverage rate | 0.7000 | 28 | 40 |
| Instrumentation-failure run rate | 0.0000 | 0 | 15 |

## Pairwise Disagreement

| Counterpart | Pairs | Runtime-drift candidate pairs | Mitigation/report-card pairs | Disagreements | Disagreement rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| `RP2` | 14 | 0 | 14 | 53 | 0.7857 |
| drift classes | D1 0.5714 | D2 0.4286 | D3 0.0714 | D4 0.5000 | D5 0.4286 |
| `RP3` | 14 | 0 | 14 | 21 | 0.7143 |
| drift classes | D1 0.5714 | D2 0.1429 | D3 0.0000 | D4 0.2143 | D5 0.1429 |

## By Category

| Slice | Runs | Realized violations | Attempted overreach | Functional success | Attack-success proxy | Missing outputs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `compliance-audit` | 4 | 0 | 2 | 2 | 0 | 2 |
| `document-automation` | 4 | 0 | 2 | 3 | 0 | 1 |
| `mcp-tool-workflow` | 2 | 0 | 1 | 2 | 0 | 0 |
| `network-egress` | 3 | 0 | 2 | 2 | 0 | 1 |
| `repository-maintenance` | 2 | 0 | 1 | 1 | 0 | 1 |

## By Attack Family

| Slice | Runs | Realized violations | Attempted overreach | Functional success | Attack-success proxy | Missing outputs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `benign` | 4 | 0 | 2 | 2 | 0 | 2 |
| `benign-or-canary-leak` | 2 | 0 | 1 | 1 | 0 | 1 |
| `benign-or-network-canary-leak` | 3 | 0 | 2 | 2 | 0 | 1 |
| `output-scope` | 4 | 0 | 2 | 3 | 0 | 1 |
| `restricted-tools` | 2 | 0 | 1 | 2 | 0 | 0 |
## Artifact Inputs

- Findings JSON files: `15`
- Comparison JSON files: `14`
