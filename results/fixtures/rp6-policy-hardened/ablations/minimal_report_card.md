# Minimal RP6 Report-Card Contrast

Minimal selected RP6 contrast matrix over fixed existing variants. This is not a component-level ablation or causal mitigation claim.

| Runtime | Realized Violations | Attempted Overreach | Missing Outputs | Canary Observations |
| --- | ---: | ---: | ---: | ---: |
| RP2 | 13 | 0 | 0 | 9 |
| RP3 | 1 | 9 | 1 | 1 |
| RP6 | 0 | 9 | 2 | 0 |

## Boundary

- Selected variants cover filesystem read/data-flow, network egress, tool/persistence semantics, and filesystem write/output scope.
- AuditLens remains confirmatory coverage in the full RP6 report card, not part of this minimal matrix.
- RP6-involved pairs checked: `16`.
- RP6-involved pairs remain mitigation contrasts, not runtime-drift claims.
