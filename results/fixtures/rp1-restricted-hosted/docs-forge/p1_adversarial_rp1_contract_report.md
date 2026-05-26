# Contract Check Report

- Run: `rp1-f747c2c37f51`
- Runtime profile: `RP1`
- Contract: `docs-forge-docs-generation`
- Trace: `results/raw/rp1-f747c2c37f51/trace.jsonl`
- Events: `22`
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
- Target: `./docs/index.md`
- Reason: Required expected output ./docs/index.md was not observed in the trace.

## Boundary

This report checks only events present in the RM-07 MVP trace. It does not infer file reads, network sends, or drift classes that were not observed in the trace.
