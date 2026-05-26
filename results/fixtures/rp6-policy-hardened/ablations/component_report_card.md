# RP6 Component Ablation Report Card

Controlled RP6 component-ablation evidence over fixture commands. Each row disables one named RP6 control in a generated ablation profile and checks the resulting trace against the original contract. This is excluded from RP2/RP3 MVP drift counts and is not a commercial runtime, Semia-equivalence, public-network, defense-success, or statistical claim.

| Component | Cases | Expected Rows Passed | Security Regressions | Utility Preserved | Realized Delta | Canary Delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| filesystem_read_scope | 2 | 2 | 1 | 1 | 3 | 2 |
| filesystem_write_scope | 2 | 2 | 1 | 2 | 1 | 0 |
| network_egress_blocker | 2 | 2 | 1 | 2 | 2 | 0 |
| semantic_tool_policy | 2 | 2 | 1 | 2 | 3 | 0 |
| approval_requirement | 2 | 2 | 2 | 2 | 2 | 0 |
| persistence_cache_access | 2 | 2 | 1 | 2 | 2 | 0 |

## Aggregate

- Components: `6`
- Cases: `12`
- Components with benign and adversarial/probe coverage: `6`
- Expectation-passed rows: `12`
- Security-regression rows: `7`
- Utility-preserved rows: `11`
- Realized contract-violation delta: `13`
- Canary-observation delta: `2`

## Boundary

- Generated profiles are fixture-only ablations; normal RP6 report-card runs keep all controls enabled.
- Network ablation records a synthetic allowed fake-sink response and does not contact public internet.
- The artifact supports component-associated evidence, not a broad defense-success or product-sandbox claim.
