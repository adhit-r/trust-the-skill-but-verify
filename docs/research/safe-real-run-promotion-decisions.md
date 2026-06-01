# Safe Real-Run Promotion Decisions

Status: decision gate for existing bounded evidence; no new live execution.

Date: 2026-06-01, Asia/Kolkata.

## Promoted Existing Slices

- `docs-forge-bounded-local-live-slices`: bounded first-party local Node
  evidence for help/version, project-local install, package materialization,
  local-tarball `npx`, and fail-closed loopback `npx` probes. This stays
  excluded from MVP runtime-drift counts.
- `ripgrep-public-live-local-binary`: partial real local `rg` binary evidence
  over a copied synthetic allowlisted workspace. This stays excluded from
  RP2/RP3 MVP runtime-drift counts.

## Blocked Candidates

The following remain blocked until a separate safe protocol exists:

- AuditLens full-product or live connector execution.
- External MCP server or connector-auth execution.
- Public-registry package acquisition.
- Credentialed API or webhook workflows.
- Commercial hosted or plugin-store runtimes.

## Verification

Run:

```sh
python3 tools/validate_safe_real_run_promotion_decisions.py
```

`make verify` runs this validator.

## Boundaries

- No new live execution is claimed by this decision.
- No public-network, credentialed, commercial-runtime, full-product,
  runtime-drift, defense-success, or completed-human-review claim is added.
- Future real-run adapters must use synthetic data, no real credentials, no
  public-network exfiltration, explicit execution-level labels, and claim-ledger
  updates before any paper-facing promotion.
