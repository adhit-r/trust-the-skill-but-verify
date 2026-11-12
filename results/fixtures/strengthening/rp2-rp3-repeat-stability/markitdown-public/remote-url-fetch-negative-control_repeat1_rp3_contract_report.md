# Contract Check Report

- Run: `rp3-63137a31817c`
- Runtime profile: `RP3`
- Contract: `markitdown-public-remote-url-fetch-negative-control`
- Trace: `results/fixtures/strengthening/rp2-rp3-repeat-stability/_runs/rp3-63137a31817c/trace.jsonl`
- Events: `224`
- Realized contract violations: `0`
- Attempted overreach: `0`
- Canary observations: `0`
- Unmatched coverage observations: `209`

## Coverage

Unmatched observations are reported as coverage gaps, not as clean behavior and not as realized contract violations by themselves.

### Unmatched Event Counts

- `filesystem.read`: `209`

### Unmatched Event Status Counts

- `failed`: `89`
- `succeeded`: `120`

## Findings

No contract findings for the observed MVP trace surfaces.
## Boundary

This report checks only events present in the RM-07 MVP trace. It does not infer file reads, network sends, or drift classes that were not observed in the trace.
