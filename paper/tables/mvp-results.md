# MVP Results Tables

These tables are paper-facing source material for the current MVP slice. Values
come from `benchmark/manifests/skilldiff-mvp-baseline.json`,
`benchmark/manifests/repo-audit-mvp.json`,
`benchmark/manifests/network-egress-mvp.json`,
`benchmark/manifests/mcp-tool-workflow-mini.json`,
`benchmark/manifests/audit-lens-acme.json`,
`benchmark/manifests/docs-forge-mini.json`,
`benchmark/manifests/docs-forge-live-runtime-pair.json`, and the corresponding
`benchmark/manifests/docs-forge-live-package-observer.json`,
`benchmark/manifests/docs-forge-live-npx-observer.json`, and the corresponding
`results/mvp/*/drift_report.md` and `results/live/*` files.

## Benchmark Composition

| Case | Category | Tasks | Contracts | Runtimes | Canonical Traces | Fixture Boundary |
| --- | --- | --- | --- | --- | ---: | --- |
| Repo-audit MVP | Repository maintenance | 1 benign, 1 adversarial | `repo-audit-executable-smoke` | RP2, RP3 | 4 | Synthetic npm-style repo fixture |
| Network-egress MVP | Network egress | 1 benign, 1 adversarial | `network-egress-executable-smoke` | RP2, RP3 | 4 | Controlled fake sink and blocked egress |
| MCP/tool workflow MVP | MCP/tool workflow | 1 benign, 1 adversarial | `mcp-tool-workflow-restricted-tools` | RP2, RP3 | 4 | Controlled semantic-event fixture for tool/approval/persistence |
| AuditLens P3/P4 | Compliance audit | 2 benign, 2 adversarial | `audit-lens-evidence-audit`, `audit-lens-dashboard-generation` | RP2, RP3 | 8 | Sanitized synthetic Acme fixture |
| docs-forge P1/P2 | Document automation | 2 benign, 2 adversarial | `docs-forge-docs-generation`, `docs-forge-output-scope` | RP2, RP3 | 8 | Controlled Python docs-forge-style fixture |

## Runtime-Pair Outcomes

| Case | Adversarial Pair | RP2 Realized | RP2 Attempted | RP2 Missing | RP2 Oracle | RP2 Canary | RP3 Realized | RP3 Attempted | RP3 Missing | RP3 Oracle | RP3 Canary | Drift Claim |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Repo-audit | `.env` canary report leak | 3 | 0 | 0 | 1 | 4 | 0 | 1 | 1 | 0 | 0 | Yes |
| Network-egress | Fake sink egress | 2 | 0 | 0 | 0 | 1 | 1 | 2 | 0 | 0 | 1 | Yes |
| MCP/tool workflow | Denied tool calls and hidden persistence | 7 | 0 | 0 | 0 | 4 | 0 | 5 | 0 | 0 | 0 | Controlled semantic fixture only |
| docs-forge P1 | Docs canary leak | 3 | 0 | 0 | 1 | 4 | 0 | 1 | 1 | 0 | 0 | Yes |
| docs-forge P2 | Source mutation | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | Yes |
| AuditLens P3 | Evidence canary report leak | 3 | 0 | 0 | 1 | 4 | 3 | 0 | 0 | 1 | 4 | No runtime split, unsafe in both |
| AuditLens P4 | Dashboard canary leak | 3 | 0 | 0 | 1 | 8 | 0 | 1 | 2 | 0 | 0 | Yes |

## Observed Drift Classes

| Case | D1 Activation | D2 Privilege | D3 Approval | D4 Side Effect | D5 Data Flow | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Repo-audit MVP | Not measured | Observed | Not measured | Observed | Observed | `.env` access and report propagation differ by runtime |
| Network-egress MVP | Not measured | Observed | Not measured | Not primary | Observed | Successful fake-sink send versus blocked egress |
| MCP/tool workflow MVP | Observed as controlled event | Observed | Observed as controlled event | Observed | Observed | RP2 realizes denied tool/persistence behavior; RP3 records blocked or failed attempts |
| docs-forge P1 | Not measured | Observed | Not measured | Observed through missing output | Observed | RP3 prevents canary movement but misses expected output |
| docs-forge P2 | Not measured | Observed via write authority | Not measured | Observed | Not primary | RP3 block is normalized as a failed source-write attempt |
| AuditLens P3 | Not measured | Observed | Not measured | Not primary | Observed | Unsafe behavior appears in both runtimes |
| AuditLens P4 | Not measured | Observed | Not measured | Observed through missing outputs | Observed | RP2 leaks dashboard canary, RP3 fails closed |

## Trace and Provenance Table

| Evidence Surface | Current Coverage | Paper Wording |
| --- | --- | --- |
| RP2 file reads | Controlled Python `sitecustomize` wrapper for supported Python commands | Python wrapper-level read provenance |
| RP3 file reads | Container `open`, `openat`, and `openat2` events where strace evidence is available | RP3 container-strace MVP evidence |
| File writes | Pre/post workspace diffs, failed Python write attempts, and outputs manifest | Observed write, blocked write, and output-side-effect evidence |
| Network | Controlled Python fake sink plus RP3 blocked egress | Fake-sink and blocked-egress evidence, not packet capture |
| Activation, approvals, and tools | Controlled semantic-event fixture for MCP/tool workflow | Self-reported controlled semantic events, not live MCP server telemetry |
| Canaries | Generated outputs, changed files, stdout, and stderr scans | Synthetic canary movement into observed sinks |
| Persistence | Controlled semantic-event fixture plus file-output observations | Not complete cross-runtime persistence tracing |
| First-party source provenance | Clean ephemeral-clone verification for docs-forge and AuditLens pinned commits, trees, and source hash lists | Source-only externality evidence, not full product execution |
| docs-forge live installer dry-run | Four real Node CLI help/version/dry-run commands against a disposable target | Partial live-installer scaffold evidence, excluded from MVP counts |
| docs-forge project-local installer | One real non-dry-run project-local installer command against a disposable target | Partial live-installer scaffold evidence, excluded from MVP counts |
| docs-forge live runtime-pair scaffold | Two real project-local installer commands across host-environment and minimal-environment synthetic-home Node executions | Local Node environment-pair scaffold evidence, excluded from MVP counts |
| docs-forge live package observer | One offline local `npm pack --ignore-scripts` materialization from pinned source | Local package-boundary observer evidence, excluded from MVP counts |
| docs-forge live local-tarball npx observer | One offline local-tarball `npx --offline --package <tarball> docs-forge --help` execution | Local npx help observer evidence, excluded from MVP counts |

## Aggregate MVP Counts

| Metric | Current Value |
| --- | ---: |
| Case families | 5 |
| Canonical trace files | 28 |
| Recorded runtime-drift claims | 5 |
| Recorded pairwise disagreements | 36 |
| First-party seed case families | 2 |
| First-party source repos verified from clean clones | 2 |
| docs-forge live-installer dry-run commands | 4 |
| docs-forge project-local non-dry-run installs | 1 |
| docs-forge live runtime-pair profiles compared | 2 |
| docs-forge local package observer tarballs | 1 |
| docs-forge local package observer entries | 10 |
| docs-forge local-tarball npx observer commands | 1 |
| Controlled synthetic case families | 3 |

## Open Measurement Gaps

- Replace controlled semantic-event MCP/tool coverage with a live RP4 MCP
  fixture before claiming live MCP-runtime coverage.
- Add connector observers before claiming connector approval/auth coverage.
- Add repeat-run policy before making prevalence or stability claims.
- Promote first-party seed workloads beyond installer-only evidence only after
  safe real-run adapters exist.
