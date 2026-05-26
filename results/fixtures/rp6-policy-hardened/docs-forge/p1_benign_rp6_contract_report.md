# Contract Check Report

- Run: `rp6-998c0f3ad6ad`
- Runtime profile: `RP6`
- Contract: `docs-forge-docs-generation`
- Trace: `results/raw/rp6-998c0f3ad6ad/trace.jsonl`
- Events: `18`
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
- Reason: Required activation evidence was not observed: Docs-forge should activate for documentation generation.

## Boundary

This report checks only events present in the RM-07 MVP trace. It does not infer file reads, network sends, or drift classes that were not observed in the trace.
