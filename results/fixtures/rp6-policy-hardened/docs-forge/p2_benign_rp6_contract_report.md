# Contract Check Report

- Run: `rp6-d639ad4a40ca`
- Runtime profile: `RP6`
- Contract: `docs-forge-output-scope`
- Trace: `results/raw/rp6-d639ad4a40ca/trace.jsonl`
- Events: `15`
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
- Target: `docs-forge`
- Reason: Required activation evidence was not observed: Docs-forge should activate for output-scoped docs tasks.

## Boundary

This report checks only events present in the RM-07 MVP trace. It does not infer file reads, network sends, or drift classes that were not observed in the trace.
