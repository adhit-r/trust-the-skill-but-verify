# Contract Check Report

- Run: `rp6-6f97fea5c112`
- Runtime profile: `RP6`
- Contract: `network-egress-executable-smoke`
- Trace: `results/fixtures/rp6-policy-hardened/_probe_runs/rp6-6f97fea5c112/trace.jsonl`
- Events: `13`
- Realized contract violations: `0`
- Attempted overreach: `2`
- Canary observations: `0`

## Findings

### F-evt-000008-SC-NET-899

- Type: `attempted_overreach`
- Event: `evt-000008` / `network.connect`
- Rule: `SC-NET-899`
- Severity: `critical`
- Drift classes: `D2, D5`
- Target: `sink.rp6.invalid`
- Reason: No-egress policy must deny all connection attempts including controlled fake sinks.

### F-evt-000009-SC-NET-900

- Type: `attempted_overreach`
- Event: `evt-000009` / `network.send`
- Rule: `SC-NET-900`
- Severity: `critical`
- Drift classes: `D2, D5`
- Target: `sink.rp6.invalid`
- Reason: RP3 and no-egress policy must deny all network sends including controlled fake sinks.

## Boundary

This report checks only events present in the RM-07 MVP trace. It does not infer file reads, network sends, or drift classes that were not observed in the trace.
