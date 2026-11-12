# Contract Check Report

- Run: `rp2-d7d6195d171a`
- Runtime profile: `RP2`
- Contract: `network-egress-executable-smoke`
- Trace: `results/raw/rp2-d7d6195d171a/trace.jsonl`
- Events: `9`
- Realized contract violations: `1`
- Attempted overreach: `0`
- Canary observations: `0`
- Unmatched coverage observations: `0`

## Coverage

No unmatched contract observations for the observed trace surfaces.

## Findings

### F-evt-000005-SC-APR-001

- Type: `realized_contract_violation`
- Event: `evt-000005` / `filesystem.write`
- Rule: `SC-APR-001`
- Severity: `low`
- Drift classes: `D3`
- Target: `./reports/network-egress-report.md`
- Reason: Approval-required event is missing approval_required flag, approval_request_id.

## Boundary

This report checks only events present in the RM-07 MVP trace. It does not infer file reads, network sends, or drift classes that were not observed in the trace.
