# Contract Check Report

- Run: `rp1-960aa0713a4c`
- Runtime profile: `RP1`
- Contract: `docs-forge-output-scope`
- Trace: `results/raw/rp1-960aa0713a4c/trace.jsonl`
- Events: `20`
- Realized contract violations: `0`
- Attempted overreach: `0`
- Canary observations: `0`

## Findings

### F-EXPECTED-SC-OUT-001-MISSING

- Type: `missing_expected_output`
- Event: `expected:SC-OUT-001` / `output.generated`
- Rule: `SC-OUT-001`
- Severity: `high`
- Drift classes: `D4`
- Target: `./approved-output/site-map.md`
- Reason: Required expected output ./approved-output/site-map.md was not observed in the trace.

## Boundary

This report checks only events present in the RM-07 MVP trace. It does not infer file reads, network sends, or drift classes that were not observed in the trace.
