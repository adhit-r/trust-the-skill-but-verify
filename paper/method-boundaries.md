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

## What Current Evidence Does Not Prove

- It does not prove that all agent skills are unsafe.
- It does not prove real-world prevalence.
- It does not execute the full docs-forge product or docs-generation workload.
- It does not execute successful or public-registry `npx` package-acquisition behavior.
- It does not execute public-registry `npx docs-forge` acquisition behavior.
- It does not execute user-scope or global docs-forge installation.
- It does not treat local Node environment-pair evidence as RP2/RP3 drift
  evidence.
- It does not execute the full AuditLens product or live connectors.
- It does not include public-internet testing.
- It does not include packet capture, DNS tracing, or arbitrary HTTP-client
  interception.
- It does not provide syscall-complete host tracing.
- It does not cover commercial hosted runtimes.
- It does not yet measure live MCP server behavior, live connector auth, or
  hidden persistence completely across arbitrary runtimes.

## Provenance Levels

| Level | Current Artifact | Safe Description | Unsafe Description |
| --- | --- | --- | --- |
| RP2 Python reads | `python_sitecustomize_wrapper_mvp` | Python wrapper-level file-open evidence for controlled Python commands | Syscall-complete host tracing |
| RP3 file reads | `container_strace_mvp` | Container `open`, `openat`, and `openat2` evidence for supported runs | Full container or host filesystem telemetry |
| Writes and outputs | Workspace diff and output manifests | Observed output and mutation evidence | Complete persistence tracing |
| Network | Fake sink and Docker network denial | Controlled fake-sink and blocked-egress evidence | Packet capture or public-internet measurement |
| Activation, approvals, and tools | Controlled semantic events in the MCP/tool workflow fixture | Deterministic fixture evidence for event representation and contract checking | Live MCP server telemetry or commercial approval UX measurement |
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
mutation, or runtime-drift claim.
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
