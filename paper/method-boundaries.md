# Method Boundaries

This file records reviewer-safe wording for the current method and artifact
state. Use it before turning the current evidence artifacts into paper prose.

## What Current Evidence Supports

- The same skill-task-contract pair can produce different observed security
  outcomes under RP2 and RP3 when repeat ID, workspace snapshot, task prompt,
  and variant ID are also held fixed.
- The framework can distinguish benign controls from adversarial variants in
  the current controlled fixtures.
- Realized violations and attempted overreach are separate measurements.
- Synthetic canary movement can be observed in generated reports, dashboards,
  logs, and changed files.
- Fake-sink network egress and blocked RP3 network attempts can be measured
  without contacting the public internet.
- Controlled semantic events can represent activation selection, deterministic
  approval records, MCP-style tool calls, and hidden persistence attempts for
  the synthetic MCP/tool workflow fixture.
- First-party seed repos can be pinned and transformed into publishable
  controlled fixtures without vendoring full source trees.
- First-party seed provenance can be rechecked from clean ephemeral clones for
  the two pinned repos, covering commit, tree, and source-hash evidence without
  turning that check into full product execution.
- Bounded docs-forge Node CLI help, version, and installer dry-run surfaces can
  be exercised against a disposable target without adding MVP runtime-drift
  counts.
- Bounded docs-forge project-local installer execution can be exercised against
  a disposable target while allowing only expected target skill/playbook writes
  and without adding MVP runtime-drift counts.
- A bounded docs-forge live Node runtime-pair scaffold can compare
  project-local installer behavior across host-environment and
  minimal-environment synthetic-home executions without changing MVP counts.
- A bounded docs-forge live package observer can materialize the pinned local
  npm package with lifecycle scripts disabled and record the tarball boundary
  without executing `npx` or package install behavior.
- A bounded docs-forge live local-tarball `npx` observer can execute
  `docs-forge --help` through `npx --offline --package <local tarball>` without
  public registry acquisition or install behavior.
- A bounded docs-forge RP3 Node container observer can execute the same
  local-tarball `npx` help workload under Docker network denial and read-only
  root filesystem constraints without changing MVP runtime-drift counts.
- A bounded docs-forge live npx runtime-pair scaffold can compare the host Node
  synthetic-home observer and RP3 Node container observer on required safety
  invariants for the benign help workload, while keeping Node/npm/cache/tarball
  differences informational.
- A bounded docs-forge adversarial package-name npx observer can execute a
  controlled `npx --yes --registry http://127.0.0.1:9/ docs-forge --help`
  probe under synthetic HOME/cache and scripts-disabled controls, observe
  fail-closed loopback-registry behavior, and keep the evidence outside MVP
  runtime-drift counts.
- A bounded docs-forge RP3 Node adversarial package-name npx observer can
  execute the same fail-closed probe against a controlled nonpublic registry
  target inside a Node-capable RP3-derived container with Docker network denial
  and a read-only root filesystem.
- A bounded docs-forge adversarial host-vs-RP3 runtime-pair scaffold can
  compare the host Node synthetic-home and RP3 Node container fail-closed
  observers on required safety invariants, while treating exact nonzero exit
  code and stderr differences as informational.
- RP6 can be exercised as a current-case mitigation/report-card pilot across
  the fourteen existing case variants, with contract-scoped wrapper-level
  filesystem/network enforcement and controlled semantic-fixture tool
  normalization. A supplemental RP6 network-denial policy probe directly
  exercises blocked `network.connect` and `network.send` events without
  changing the fixed current-case variants.
- A static scanner baseline, Semia-style reachability approximation,
  ClawGuard/Task Shield-style action-boundary baseline, contract-derived
  least-privilege baseline, coarse RP2/RP3/RP6 mitigation ladder, and minimal
  RP6 report-card contrast can be reported as strengthening evidence outside
  the RP2/RP3 MVP aggregate counts.
- A bounded RP6 component-ablation report card can be reported for six named
  RP6 controls across twelve generated ablation traces. Each ablation disables one
  named fixture control in a generated RP6 profile and checks the resulting
  trace against the original contract; this is component-level fixture evidence,
  not product-scale defense causality.
- A bounded deterministic RP6 repeat-stability check can be reported for the
  fourteen current controlled RP6 fixtures across repeat IDs 1, 2, and 3. It is
  not prevalence, statistical, or model-mediated stability evidence.
- A bounded RP5 plugin-style fixture can be reported for local synthetic plugin
  metadata, activation selection, one non-activation negative control,
  fixture install/update behavior, bundled-resource reads, fixture host API
  calls, scoped plugin storage, generated outputs, and cleanup.

## What Current Evidence Does Not Prove

- It does not prove that all agent skills are unsafe.
- It does not prove real-world prevalence.
- It does not execute the full docs-forge product or docs-generation workload.
- It does not execute successful or public-registry `npx` package-acquisition behavior.
- It does not execute public-registry `npx docs-forge` acquisition behavior.
- It does not execute user-scope or global docs-forge installation.
- It does not treat local Node environment-pair evidence as RP2/RP3 drift
  evidence.
- It does not treat adversarial package-name npx fail-closed pair evidence as
  an added runtime-drift finding.
- It does not execute the full AuditLens product or live connectors.
- It does not include public-internet testing.
- It does not include packet capture, DNS tracing, or arbitrary HTTP-client
  interception.
- It does not treat RP6-vs-RP2/RP3 report-card comparisons as runtime-drift
  claims.
- It does not provide syscall-complete host tracing.
- It does not cover commercial hosted runtimes.
- It does not cover commercial plugin-store behavior, live host API behavior,
  external MCP/server plugin behavior, or public-network plugin behavior.
- It does not measure external MCP server behavior, live connector auth,
  commercial MCP-client behavior, or hidden persistence completely across
  arbitrary runtimes.
- It does not prove RP6 is a successful defense. The current RP6 evidence is a
  bounded report card that must be read with task success and missing-output
  counts.
- It does not provide product-scale causal RP6 defense evidence. The current
  component ablations are controlled fixture ablations only.
- It does not support repeat-run statistical stability claims; the current RP6
  repeat evidence supports only bounded deterministic stability for controlled
  RP6 fixtures.
- It does not treat static scanner, reachability approximation, or
  action-boundary baseline artifacts as added RP2/RP3 runtime-drift evidence.
- It does not claim Semia equivalence or Semia reproduction.
- It does not claim live command/tool guardrail UX efficacy, ClawGuard
  reproduction, or Task Shield reproduction.

## Provenance Levels

| Level | Current Artifact | Safe Description | Unsafe Description |
| --- | --- | --- | --- |
| RP2 Python reads | `python_sitecustomize_wrapper_mvp` | Python wrapper-level file-open evidence for controlled Python commands | Syscall-complete host tracing |
| RP3 file reads | `container_strace_mvp` | Container `open`, `openat`, and `openat2` evidence for supported runs | Full container or host filesystem telemetry |
| Writes and outputs | Workspace diff and output manifests | Observed output and mutation evidence | Complete persistence tracing |
| Network | Fake sink and Docker network denial | Controlled fake-sink and blocked-egress evidence | Packet capture or public-internet measurement |
| Activation, approvals, and tools | Controlled semantic events in the MCP/tool workflow fixture | Deterministic fixture evidence for event representation and contract checking | Live MCP server telemetry or commercial approval UX measurement |
| RP4 local MCP fixture | `rp4-mcp-connected-mini` traces and contract findings | Bounded local MCP descriptor, resource-read, tool-call, approval, blocked-attempt, canary, and cleanup evidence | External MCP server telemetry, connector auth, commercial MCP-client behavior, or runtime-drift evidence |
| RP5 plugin-style fixture | `results/fixtures/rp5-plugin-style/report_card.json` plus RP5 traces and contract findings | Bounded local plugin manifest, activation, non-activation, install-hook, update-metadata, fixture host API, scoped storage, output, and cleanup evidence | Commercial plugin-store behavior, live host API behavior, external MCP/server behavior, public-network plugin evidence, or defense-success evidence |
| RP6 policy-hardened report card | `results/fixtures/rp6-policy-hardened/report_card.json` plus RP6 traces and the supplemental network policy probe | Current-case mitigation report-card pilot with wrapper-level controlled Python enforcement, direct fake-sink network-denial probe evidence, and controlled semantic-fixture tool normalization | Defense success, syscall-complete hardening, commercial-runtime behavior, public-network evidence, or RP6-vs-RP2/RP3 runtime-drift evidence |
| Strengthening baselines | `results/fixtures/strengthening/index.json` and `results/fixtures/rp6-policy-hardened/ablations/component_report_card.json` | Static/source-only scanner baseline, bounded reachability approximation, action-relevance mitigation baseline, contract-derived least-privilege budget, coarse RP2/RP3/RP6 mitigation ladder, minimal RP6 contrast, bounded component-ablation fixture evidence, and bounded deterministic RP6 repeat stability | Runtime evidence from static scans, Semia equivalence, ClawGuard/Task Shield reproduction, product-scale defense causality, defense success, live guardrail UX efficacy, or repeat-run statistical/model-mediated stability |
| Canaries | Output/log/change scanning | Synthetic canary movement in observed sinks | Real secret exfiltration evidence |
| First-party source provenance | Clean ephemeral clones checked against pinned manifests | Source-provenance evidence for seed realism and artifact reproducibility | Full product execution or runtime-drift evidence |
| docs-forge live installer dry-run | `node bin/docs-forge.js` help, version, and installer dry-run commands | Partial live CLI dry-run evidence with source/target pre/post checks | Full installer execution, `npx` safety, network absence under packet capture, or runtime-drift evidence |
| docs-forge project-local installer | One non-dry-run `node bin/docs-forge.js install --agents claude,antigravity,universal --scope project` command against a disposable target | Partial live installer evidence with Node filesystem-call instrumentation and source/target/home pre/post checks | Docs generation, `npx` safety, user/global install behavior, packet-capture network absence, or runtime-drift evidence |
| docs-forge live runtime-pair scaffold | Host-environment and minimal-environment synthetic-home Node executions of the same project-local installer command | Bounded local Node environment-pair comparison with matching target/output hashes, excluded from MVP counts | RP2/RP3 drift evidence, commercial runtime evidence, docs generation, `npx` package acquisition, or complete Node/runtime tracing |
| docs-forge live package observer | Local `npm pack --ignore-scripts` materialization of the pinned source package into an ephemeral package directory | Offline package-boundary evidence for the tarball and expected entry list, excluded from MVP counts | `npx` execution, registry acquisition, install behavior, public-internet safety under packet capture, or runtime-drift evidence |
| docs-forge live local-tarball npx observer | Local `npx --yes --offline --package <tarball> docs-forge --help` after local package materialization | Bounded offline local-tarball npx help evidence, excluded from MVP counts | Public registry acquisition, package-name `npx docs-forge`, install behavior, docs generation, packet-capture network evidence, or runtime-drift evidence |
| docs-forge RP3 Node local-tarball npx observer | Containerized `npx --yes --offline --package <tarball> docs-forge --help` in `skilldiff-rp3-node` with Docker `--network=none` and `--read-only` | Bounded RP3-style container npx help evidence, excluded from MVP counts | Packet capture, public registry acquisition, package-name `npx docs-forge`, install behavior, docs generation, or RP2/RP3 drift evidence |
| docs-forge live npx runtime-pair scaffold | Host Node synthetic-home and RP3 Node container executions of local-tarball `npx --offline` help | Bounded pair comparison for benign help workload safety invariants, excluded from MVP counts | Runtime-drift claim, adversarial npx/package-acquisition study, public registry evidence, or packet-capture evidence |
| docs-forge adversarial package-name npx observer | Host Node synthetic-home execution of `npx --yes --registry http://127.0.0.1:9/ docs-forge --help` | Bounded fail-closed package-name npx probe against a loopback registry, excluded from MVP counts | Public registry acquisition, successful package acquisition, package install behavior, lifecycle-script execution, packet-capture evidence, or runtime-drift evidence |
| docs-forge RP3 Node adversarial package-name npx observer | Containerized `npx --yes --registry http://127.0.0.1:9/ docs-forge --help` in `skilldiff-rp3-node` with Docker `--network=none` and `--read-only` | Bounded fail-closed package-name npx probe against a controlled nonpublic registry target, excluded from MVP counts | Public registry acquisition, packet capture, successful package acquisition, package install behavior, lifecycle-script execution, or runtime-drift evidence |
| docs-forge adversarial npx runtime-pair scaffold | Host Node synthetic-home and RP3 Node container executions of the same fail-closed package-name npx probe | Bounded pair comparison for adversarial fail-closed safety invariants, excluded from MVP counts | Public npm acquisition evidence, packet-capture coverage, successful install behavior, or an added runtime-drift finding |

## Network Evidence Boundary

Benchmark network tests must not contact the public internet. RP2 fake-sink
runs record payload hashes, byte counts, redaction flags, and canary labels.
RP3 blocked-egress runs record denied destinations and failed or blocked
network status. Raw request bodies, raw query strings, sensitive headers, and
real secrets are outside the safe artifact boundary.

## Approval, Tool, and Persistence Boundary

The MCP/tool workflow pilot evaluates activation, approval, tool-call, and
persistence representation through controlled semantic events. The paper can
claim those surfaces are now traceable and contract-checkable for that fixture.
It should not claim live MCP server coverage, real connector auth, commercial
approval UX behavior, or complete persistence tracing.

The RP4 S1.2 fixture extends that boundary to a local MCP-connected profile:
the artifact emits descriptor, approved resource-read, approved tool-call,
blocked discovery/auth/exec, blocked canary-bearing tool-message, run-scoped
persistence, output, and cleanup events. MCP behavior is represented as
`tool.call` plus MCP metadata under the current trace schema. This is still
local fixture evidence, not external MCP server telemetry, connector-auth
evidence, commercial-client evidence, or an added runtime-drift finding.

The RP5 S1.4 fixture extends the same controlled semantic-event boundary to a
plugin-style profile: the artifact emits plugin manifest discovery, activation
selection, `activation.not_selected` for an unrelated negative control, fixture
install-hook execution, fixture host API calls, local update metadata checks,
run-scoped plugin storage, generated outputs, and cleanup. This is still local
fixture evidence, not commercial plugin-store telemetry, live host API
behavior, external MCP/server behavior, public-network plugin evidence, or a
defense-success claim.

The RP6 S1.3 current-case report card applies contract-derived wrapper-level
policy to the existing fourteen case variants. It records zero realized
contract violations, twelve blocked attempted-overreach findings, seven
missing expected outputs, and zero canary observations. It also includes one
supplemental network-denial policy probe with blocked `network.connect` and
`network.send` findings. This is useful mitigation evidence only when reported
with task success and missing outputs; it is not a standalone defense-success
or RP6 runtime-drift claim.

The strengthening package adds a static scanner baseline over controlled
fixture skill text/scripts, a Semia-style reachability approximation over
static signals and contract deny surfaces, a ClawGuard/Task Shield-style
action-boundary relevance baseline over controlled fixture commands, a
contract-derived least-privilege budget, a coarse RP2/RP3/RP6 mitigation
ladder, a minimal selected RP6 contrast matrix, six generated RP6 component
ablation profiles, and a bounded deterministic RP6 repeat-stability check over
repeat IDs 1, 2, and 3. The component ablation
artifact covers filesystem read scope, filesystem write scope, network egress
blocking, semantic tool policy, approval requirements, and file-backed
persistence/cache access across twelve generated RP6 traces. These artifacts
improve reviewer-facing baselines, but they still do not support Semia
equivalence or reproduction, ClawGuard/Task Shield reproduction, live guardrail
efficacy, product-scale defense causality, defense success, or
statistical/model-mediated repeat stability.

## Reviewer-Safe Claim

We introduce differential runtime security testing for portable agent skills:
given a skill, task, contract, fixed task prompt, fixed workspace snapshot,
variant, repeat ID, and runtime profile, the framework executes controlled
benign and adversarial variants, records normalized traces, and compares
whether violations are realized, blocked, or converted into missing outputs
across runtimes. In the current baseline evidence, five controlled case
families produce five runtime-drift claims across RP2 and RP3, while preserving
explicit boundaries around provenance, network evidence, product execution, and
safe publication.

The first-party source-provenance artifact separately verifies that the pinned
docs-forge and AuditLens source repositories match their published commits,
trees, and source hash lists from clean ephemeral clones. The docs-forge
live-installer artifact then exercises bounded Node CLI help, version, and
dry-run installer surfaces against a disposable target. A separate docs-forge
live project-local installer artifact exercises the pinned Node CLI against a
disposable target and verifies only expected project-local skill/playbook
writes. The docs-forge live runtime-pair scaffold then compares the same
project-local installer command under host-environment and minimal-environment
synthetic-home Node executions, with no target-output disagreement and no
source/home mutation. The docs-forge live package observer materializes the
local npm package from pinned source with lifecycle scripts disabled and records
the expected tarball boundary. The docs-forge local-tarball npx observer then
executes `docs-forge --help` through `npx --offline --package <local tarball>`.
The docs-forge RP3 Node container observer runs the same local-tarball help
workload in a Node-capable RP3-derived image with Docker network denial and a
read-only root filesystem. The docs-forge live npx runtime-pair scaffold then
compares the host Node and RP3 Node observer outputs and required safety
invariants without treating informational Node/npm/cache/tarball differences
as drift. The docs-forge adversarial package-name npx observer then executes a
loopback-registry `npx docs-forge --help` probe and observes fail-closed
behavior with no successful acquisition, install, lifecycle, source/home
mutation, or runtime-drift claim. The RP3 Node adversarial observer runs the
same package-name npx fail-closed probe inside a Node-capable RP3-derived
container with Docker network denial and a read-only root filesystem. The
adversarial npx runtime-pair scaffold then compares the host and RP3
fail-closed observers on required safety invariants and records zero required
pair-check failures without adding a runtime-drift claim.
The RP6 policy-hardened report card separately runs the existing fourteen
current-case variants, adds one supplemental network-denial policy probe, and
is excluded from the RP2/RP3 MVP aggregate counts.
These artifacts do not support claims about public registry package
acquisition, public-registry package-name `npx docs-forge`, full docs generation,
global/user-scope installation, RP2/RP3 runtime drift, the full AuditLens
product, connector auth flows, or live SaaS exports.

## Reviewer-Risky Wording To Avoid

- "The benchmark proves agent skills are unsafe."
- "The Docker runtime prevents all leakage."
- "The trace harness captures every file read."
- "Network exfiltration was observed on the internet."
- "docs-forge was fully executed."
- "AuditLens connector behavior was evaluated."
- "Live MCP server behavior was evaluated."
- "Approval drift is measured outside the controlled MCP/tool fixture."
- "Clean source verification proves full-product runtime behavior."
