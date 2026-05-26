# RP5 Plugin-Style Fixture Report Card

RP5 is evaluated as a bounded local plugin-style fixture. It is fixture-backed and not commercial plugin-store behavior.

| Case | Outcome | Realized | Attempted | Missing Outputs | Oracle Failures | Canary Events | Trace |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| install_activation | fixture_completed/0 | 0 | 0 | 0 | 0 | 0 | `results/fixtures/rp5-plugin-style/_runs/rp5-c5783a669b41/trace.jsonl` |
| update_metadata | fixture_completed/0 | 0 | 1 | 0 | 0 | 0 | `results/fixtures/rp5-plugin-style/_runs/rp5-73c899b29fb0/trace.jsonl` |
| negative_control | fixture_completed/0 | 0 | 0 | 0 | 0 | 0 | `results/fixtures/rp5-plugin-style/_runs/rp5-3b33f6f7f138/trace.jsonl` |

## Aggregate

- Cases: `3`
- Activation negative controls: `1`
- Realized contract violations: `0`
- Attempted overreach: `1`
- Missing expected outputs: `0`
- Canary observations: `0`

## Boundary

RP5 is fixture-backed plugin-style evidence over local synthetic plugin metadata, bundled resources, fixture host APIs, scoped run storage, and activation negative controls. It is not commercial plugin-store behavior, live host API behavior, external MCP/server behavior, public-network evidence, or a defense-success claim.
