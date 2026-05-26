# Benchmark Data Card

## Scope

This data card covers the current SkillDiff benchmark fixtures and derived
artifacts. The current package is a controlled feasibility and method-evidence
artifact, not a full 40/120 paper benchmark and not ecosystem prevalence
evidence.

## Included Data

- Synthetic workspaces for repository maintenance, API-style fake-sink
  workflow, MCP/tool workflow, compliance/audit, and document automation.
- Task prompts, security contracts, expected-output metadata, synthetic
  canaries, runtime profiles, traces, contract findings, comparisons, and
  derived runtime report cards.
- First-party source provenance metadata and pinned source hash lists where
  applicable.

## Excluded Data

- Real secrets, cookies, SSH keys, API tokens, connector credentials, auth
  state, customer data, and live SaaS exports.
- Public exfiltration endpoints or packet-capture datasets.
- Full first-party source trees unless a future release explicitly changes the
  publication boundary.

## Provenance Levels

- `synthetic`: benchmark-owned synthetic fixture.
- `local_inspection_plus_controlled_fixture`: source inspected or pinned, but
  runtime evidence uses a controlled fixture.
- `first_party_sanitized_fixture`: first-party seed source is represented by a
  sanitized publishable fixture.

## Execution Levels

Execution labels distinguish controlled Python fixtures, local fake-sink
fixtures, semantic event fixtures, live bounded observers, and source-only
metadata. Aggregates must not mix these levels without preserving the label.

## Safety Labels

Publishable cases must use synthetic-only canaries, set real-secret presence
to false, declare denied sinks, and list excluded claims.
