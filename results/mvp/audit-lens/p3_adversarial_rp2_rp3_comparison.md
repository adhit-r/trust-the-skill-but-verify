# Contract Run Comparison

## Summary

| Runs | Pairs | Runtime Profiles | Contracts | Pairwise Disagreements | Runtime Drift Claims |
| ---: | ---: | --- | --- | ---: | ---: |
| 2 | 1 | `RP2, RP3` | `audit-lens-evidence-audit` | 0 | 0 |

## Per-Run Counts

| Run | Runtime | Contract | Events | Findings | Realized Violations | Attempted Overreach | Canary Observations | Drift Classes |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `rp2-2a618a308d4f` | `RP2` | `audit-lens-evidence-audit` | 29 | 4 | 3 | 0 | 4 | `D2, D4, D5` |
| `rp3-0fb2f0af2dd4` | `RP3` | `audit-lens-evidence-audit` | 248 | 4 | 3 | 0 | 4 | `D2, D4, D5` |

## Pairwise Disagreements

### `rp2-2a618a308d4f` vs `rp3-0fb2f0af2dd4`

- Runtime profiles: `RP2` vs `RP3`
- Classification: `no_pairwise_disagreement`
- Boundary: Runtime profiles differ, but this pair has no finding-set disagreement in the observed contract-check output.
- Shared findings: `4`
- Disagreements: `0`
- Summary delta (right minus left): realized violations `0`, attempted overreach `0`, canary observations `0`, events `219`

#### Only in left

None.

#### Only in right

None.

## Boundary

This utility compares existing contract-check outputs. It can identify pairwise disagreement in observed findings, but it does not prove runtime-induced drift unless the compared runs are the same skill-task, fixtures, and prompt variant under different runtime profiles.
