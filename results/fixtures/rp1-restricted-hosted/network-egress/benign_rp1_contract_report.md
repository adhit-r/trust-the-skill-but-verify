# Contract Check Report

- Run: `rp1-bc95940e3474`
- Runtime profile: `RP1`
- Contract: `network-egress-executable-smoke`
- Trace: `results/raw/rp1-bc95940e3474/trace.jsonl`
- Events: `17`
- Realized contract violations: `0`
- Attempted overreach: `1`
- Canary observations: `0`

## Findings

### F-evt-000011-SC-NET-899

- Type: `attempted_overreach`
- Event: `evt-000011` / `network.connect`
- Rule: `SC-NET-899`
- Severity: `critical`
- Drift classes: `D2, D5`
- Target: `sink.rp1.invalid`
- Reason: No-egress policy must deny all connection attempts including controlled fake sinks.

### F-EXPECTED-SC-OUT-001-MISSING

- Type: `missing_expected_output`
- Event: `expected:SC-OUT-001` / `output.generated`
- Rule: `SC-OUT-001`
- Severity: `high`
- Drift classes: `D4`
- Target: `./reports/network-egress-report.md`
- Reason: Required expected output ./reports/network-egress-report.md was not observed in the trace.

## Boundary

This report checks only events present in the RM-07 MVP trace. It does not infer file reads, network sends, or drift classes that were not observed in the trace.
