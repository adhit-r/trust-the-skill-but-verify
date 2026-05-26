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
`benchmark/manifests/docs-forge-live-npx-observer.json`,
`benchmark/manifests/docs-forge-live-npx-rp3-node-observer.json`,
`benchmark/manifests/docs-forge-live-npx-runtime-pair.json`,
`benchmark/manifests/docs-forge-live-npx-adversarial-package-acquisition.json`,
`benchmark/manifests/docs-forge-live-npx-rp3-node-adversarial-package-acquisition.json`,
`benchmark/manifests/docs-forge-live-npx-adversarial-package-acquisition-runtime-pair.json`,
`benchmark/manifests/rp1-restricted-hosted-mvp.json`,
`benchmark/manifests/rp5-plugin-style-mvp.json`,
`benchmark/manifests/rp6-policy-hardened-mvp.json`, and the corresponding
`results/mvp/*/drift_report.md`, `results/fixtures/rp1-restricted-hosted/*`,
`results/fixtures/rp5-plugin-style/*`,
`results/fixtures/rp6-policy-hardened/*`,
and `results/live/*` files.

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

## RP6 Current-Case Report Card

RP6 is not folded into the RP2/RP3 MVP aggregate counts. It is a bounded
mitigation/report-card pilot over the same fourteen current-case variants.
It also includes one supplemental network-denial policy probe so blocked
network enforcement is directly evidenced without changing the fixed
current-case variants.

| Metric | RP6 Current-Case Value |
| --- | ---: |
| Case variants | 14 |
| Completed cases | 8 |
| Realized contract violations | 0 |
| Blocked attempted-overreach findings | 12 |
| Missing expected outputs | 7 |
| Canary observations | 0 |
| Supplemental network-denial policy probes | 1 |
| Network-denial probe blocked connect/send findings | 2 |

## RP1 Restricted-Hosted Simulator Report Card

RP1 is not folded into the RP2/RP3 MVP aggregate counts. It is a deterministic
restricted-hosted simulator over the upload-oriented current-case subset and is
not commercial hosted-runtime behavior, live provider instrumentation, live
MCP/plugin behavior, or public-network evidence. The current subset excludes
MCP/tool workflow because RP1 disables MCP/plugin APIs.

| Metric | RP1 Simulator Value |
| --- | ---: |
| Case variants | 12 |
| Simulated completed cases | 12 |
| Realized contract violations | 0 |
| Blocked attempted-overreach findings | 2 |
| Missing expected outputs | 16 |
| Canary observations | 0 |

## RP5 Plugin-Style Fixture Report Card

RP5 is not folded into the RP2/RP3 MVP aggregate counts. It is a bounded local
plugin-style fixture that exercises synthetic plugin metadata, activation
selection, one non-activation negative control, fixture install/update
behavior, bundled-resource reads, fixture host APIs, scoped plugin storage,
generated outputs, and cleanup. It is not commercial plugin-store behavior,
live host API behavior, external MCP/server behavior, public-network evidence,
or a defense-success claim.

| Metric | RP5 Fixture Value |
| --- | ---: |
| Case variants | 3 |
| Fixture completed cases | 3 |
| Activation negative controls | 1 |
| Realized contract violations | 0 |
| Blocked attempted-overreach findings | 1 |
| Missing expected outputs | 0 |
| Canary observations | 0 |

## Strengthening Baselines

These artifacts are outside the RP2/RP3 MVP aggregate counts and do not create
new runtime-drift claims.

| Artifact | Scope | Key Result |
| --- | --- | --- |
| Static scanner baseline | 14 variants, 48 controlled fixture skill/README files | Source-only scanner produced 88 static findings across all 14 cases; excluded from runtime evidence and prevalence claims |
| Semia-style reachability approximation | 14 variants, 88 static findings considered | 88 bounded approximation candidates; Semia equivalence, Semia reproduction, and runtime-confirmation claims supported: 0 |
| ClawGuard/Task Shield-style action-boundary baseline | 14 controlled fixture commands | 14/14 commands are contract-allowed and fixture-scoped with 0 review flags; not a ClawGuard or Task Shield reproduction |
| Contract-derived least-privilege baseline | 14 variants, 7 contracts | 7/7 benign expectations and 7/7 adversarial fail-closed expectations pass against RP6 outcomes |
| RP1 restricted-hosted simulator report card | 12 variants across 4 upload-oriented families | Valid simulator traces with zero realized violations and explicit missing-output utility cost; excluded from RP2/RP3 MVP counts |
| RP5 plugin-style fixture report card | 3 plugin-style variants | Valid fixture traces with one activation negative control, zero realized violations, one blocked attempted-overreach finding, and zero missing outputs; excluded from RP2/RP3 MVP counts |
| Coarse RP2/RP3/RP6 mitigation ladder | 14 variants | Observed counts: RP2 has 22 realized violations and 25 canary observations; RP6 has 0 realized violations, 0 canary observations, and 7 additional missing outputs relative to RP2 |
| Minimal RP6 report-card contrast | 8 selected variants plus 1 network policy probe | RP2 to RP6 realized violations drop 13 to 0; canary observations drop 9 to 0; RP6 missing outputs increase by 2 |
| RP6 component-ablation report card | 6 controls, 12 generated RP6 ablation traces | Every component has benign and adversarial/probe coverage; disabling controls adds 13 realized violations and 2 canary observations relative to fully enforced RP6 baselines |
| RP6 deterministic repeat-stability check | 14 variants, repeat IDs 1/2/3, 42 observations | 14/14 outcome summaries match including and excluding event count; statistical repeat-stability claims supported: 0 |

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
| docs-forge RP3 Node local-tarball npx observer | One containerized local-tarball `npx --offline --package <tarball> docs-forge --help` execution under Docker `--network=none` and `--read-only` | RP3-style container npx help observer evidence, excluded from MVP counts |
| docs-forge live npx runtime-pair scaffold | Host Node synthetic-home and RP3 Node container local-tarball npx observers compared on required safety invariants | Local npx pair scaffold evidence, excluded from MVP counts |
| docs-forge adversarial package-name npx observer | One `npx --yes --registry http://127.0.0.1:9/ docs-forge --help` fail-closed probe | Loopback-registry package-name npx evidence, excluded from MVP counts |
| docs-forge RP3 Node adversarial package-name npx observer | One containerized `npx --yes --registry http://127.0.0.1:9/ docs-forge --help` fail-closed probe under Docker `--network=none` and `--read-only` | RP3-style controlled nonpublic registry package-name npx evidence, excluded from MVP counts |
| docs-forge adversarial npx runtime-pair scaffold | Host Node synthetic-home and RP3 Node container package-name npx fail-closed observers compared on required safety invariants | Adversarial npx pair scaffold evidence, excluded from MVP counts |
| RP1 restricted-hosted simulator | Twelve deterministic simulator traces over the upload-oriented current subset | Simulator-backed report-card evidence, excluded from RP2/RP3 MVP counts and not hosted-provider behavior |
| RP5 plugin-style fixture | Three deterministic fixture traces over install activation, update metadata, and non-activation negative control | Fixture-backed plugin lifecycle evidence, excluded from RP2/RP3 MVP counts and not commercial plugin-store or live host API behavior |
| RP6 policy-hardened current-case report card | Fourteen RP6 controlled Python/semantic-fixture runs over the existing current-case variants | Mitigation report-card pilot evidence, excluded from RP2/RP3 MVP counts and not a defense-success claim |
| Static scanner baseline | Source-only scan of controlled fixture skill text/scripts and workspace README files | Static/source-only classifier baseline, not runtime evidence, vulnerability proof, or prevalence evidence |
| Semia-style reachability approximation | Static signals joined to SkillDiff contract deny surfaces | Bounded reachability approximation, not Semia equivalence, Semia reproduction, runtime confirmation, or prevalence evidence |
| Action-boundary baseline | Controlled fixture commands checked against contract shell allow rules and task-scope relevance | Bounded action-relevance mitigation baseline, not live product guardrail efficacy or ClawGuard/Task Shield reproduction |
| RP6 component ablations | Twelve generated RP6 ablation traces across filesystem read, filesystem write, network egress, semantic tool policy, approval requirements, and file-backed persistence/cache access | Component-level fixture evidence, excluded from RP2/RP3 MVP counts and not product-scale defense causality |

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
| docs-forge RP3 Node local-tarball npx observer workload commands | 2 |
| docs-forge live npx runtime-pair profiles compared | 2 |
| docs-forge adversarial package-name npx fail-closed commands | 1 |
| docs-forge adversarial loopback registry events | 1 |
| docs-forge RP3 Node adversarial package-name npx total commands | 2 |
| docs-forge adversarial npx runtime-pair profiles compared | 2 |
| docs-forge adversarial npx runtime-pair required check failures | 0 |
| RP1 simulator current-subset variants | 12 |
| RP1 simulator realized contract violations | 0 |
| RP1 simulator attempted-overreach findings | 2 |
| RP1 simulator missing expected outputs | 16 |
| RP1 simulator canary observations | 0 |
| RP5 plugin-style fixture variants | 3 |
| RP5 plugin-style activation negative controls | 1 |
| RP5 plugin-style realized contract violations | 0 |
| RP5 plugin-style attempted-overreach findings | 1 |
| RP5 plugin-style missing expected outputs | 0 |
| RP5 plugin-style canary observations | 0 |
| RP6 current-case report-card variants | 14 |
| RP6 current-case realized contract violations | 0 |
| RP6 current-case attempted-overreach findings | 12 |
| RP6 current-case missing expected outputs | 7 |
| RP6 supplemental network-denial policy probes | 1 |
| RP6 supplemental network-denial blocked findings | 2 |
| Least-privilege baseline case variants | 14 |
| Least-privilege benign expectation passes | 7 |
| Least-privilege adversarial expectation passes | 7 |
| Minimal RP6 contrast variants | 8 |
| RP6 component-ablation controls | 6 |
| RP6 component-ablation traces | 12 |
| RP6 component-ablation realized-violation delta | 13 |
| RP6 component-ablation canary-observation delta | 2 |
| RP6 repeat-stability variants | 14 |
| RP6 repeat-stability observations | 42 |
| RP6 bounded deterministic stability claims supported | 14 |
| Statistical repeat-stability claims currently supported | 0 |
| Controlled synthetic case families | 3 |

## Open Measurement Gaps

- Treat RP1 as deterministic simulator evidence only unless a future live-hosted
  adapter produces direct provider measurements.
- Promote RP4 beyond bounded local fixture evidence before claiming external
  MCP server, connector-auth, commercial-client, or MCP-runtime coverage.
- Promote RP5 beyond bounded local fixture evidence before claiming commercial
  plugin-store behavior, live host API behavior, external MCP/server behavior,
  or public-network plugin evidence.
- Promote RP6 beyond current-case report-card and bounded fixture-ablation
  evidence only after utility-preserving mitigation checks scale beyond the
  current controlled cases. RP6 comparison files label RP6-vs-RP2/RP3 pairs as
  mitigation-report-card contrasts, not runtime-drift claims.
- Add connector observers before claiming connector approval/auth coverage.
- Expand repeat-run policy beyond the current bounded RP6 deterministic fixture
  stability check before making prevalence, statistical, or model-mediated
  stability claims.
- Promote first-party seed workloads beyond installer-only evidence only after
  safe real-run adapters exist.
