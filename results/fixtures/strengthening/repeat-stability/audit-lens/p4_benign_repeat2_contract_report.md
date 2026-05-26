# Contract Check Report

- Run: `rp6-be3252d49e97`
- Runtime profile: `RP6`
- Contract: `audit-lens-dashboard-generation`
- Trace: `results/fixtures/strengthening/repeat-stability/_runs/rp6-be3252d49e97/trace.jsonl`
- Events: `31`
- Realized contract violations: `0`
- Attempted overreach: `0`
- Canary observations: `0`

## Findings

### F-ACTIVATION-SC-ACT-001

- Type: `missing_activation`
- Event: `activation:SC-ACT-001` / `activation.select`
- Rule: `SC-ACT-001`
- Severity: `low`
- Drift classes: `D1`
- Target: `audit-lens`
- Reason: Required activation evidence was not observed: Audit-lens dashboard skill should activate for dashboard generation.

## Boundary

This report checks only events present in the RM-07 MVP trace. It does not infer file reads, network sends, or drift classes that were not observed in the trace.
