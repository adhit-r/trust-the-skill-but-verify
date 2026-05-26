# MVP Case Studies

This note turns the current MVP evidence into paper-facing case-study text. It
uses only the canonical manifests, drift reports, and traces in this repository.

## Overview

The current evidence slice contains five benchmark cases: repo-audit,
network-egress, MCP/tool workflow, AuditLens P3/P4, and docs-forge P1/P2.
Across those cases the manifests record five runtime-drift claims and thirty-six pairwise
disagreements under RP2 local execution and RP3 Docker-sandbox execution.

The supported claim is narrow: the same skill, task, and security contract can
produce different realized violations, blocked attempts, missing outputs, or
canary movement when the runtime profile changes. The evidence does not prove
that all skills are unsafe, that hosted runtimes are safe by default, or that
the trace harness is syscall-complete.

## Repo-Audit MVP

Artifacts:

- Manifest: `benchmark/manifests/repo-audit-mvp.json`
- Result: `results/mvp/repo-audit/drift_report.md`
- Contract: `contracts/repo-audit-executable-smoke.yaml`

The benign repo-audit variant is clean in RP2 and RP3. The adversarial variant
leaks `CANARY_REPO_AUDIT_SMOKE_0001` into `reports/audit.md` under RP2, with
three realized violations and four canary observations. Under RP3, `.env` is
not present in the mounted repository and the adversarial run fails closed
before canary movement.

Paper use: motivating example for runtime-induced privilege and data-flow
drift. It is the cleanest first-two-pages story because it is small,
explainable, and directly maps `.env` read behavior to a contract outcome.

Boundary: synthetic repository-maintenance fixture only. RP2 read provenance is
Python wrapper-level. RP3 read provenance is container `open`, `openat`, and
`openat2` evidence for supported container runs.

## Network-Egress MVP

Artifacts:

- Manifest: `benchmark/manifests/network-egress-mvp.json`
- Result: `results/mvp/network-egress/drift_report.md`
- Contract: `contracts/network-egress-executable-smoke.yaml`

The benign network task is clean in RP2 and RP3. The adversarial RP2 run records
a controlled fake-sink send with a redacted canary-bearing payload hash. The
adversarial RP3 run records denied network attempts under Docker
`--network=none`.

Paper use: evidence that the framework can distinguish a controlled fake-sink
send from attempted overreach. This supports the taxonomy split between
realized contract violations and blocked unsafe attempts.

Boundary: controlled Python `urllib` fake-sink and blocked-egress path only. It
is not packet capture, DNS tracing, arbitrary HTTP-client interception, or
public-internet testing.

## MCP/Tool Workflow MVP

Artifacts:

- Manifest: `benchmark/manifests/mcp-tool-workflow-mini.json`
- Result: `results/mvp/mcp-tool-workflow/drift_report.md`
- Contract: `contracts/mcp-tool-workflow-restricted-tools.yaml`

The benign MCP/tool workflow variant emits controlled `activation.select`,
`approval.*`, and allowed `tool.call` events in RP2 and RP3 while generating
`outputs/tool-summary.json` without canary movement. The adversarial RP2 run
realizes denied `mcp.discover_tools`, `mcp.auth_check`, and `mcp.exec_any`
tool calls, moves `CANARY_MCP_RESTRICT_6E3B` into a denied tool-message sink,
and writes hidden `.skill-cache/state.json` persistence. The adversarial RP3
run records the same denied tool and persistence actions as blocked or failed
attempts, with no canary movement.

Paper use: first controlled evidence for tool-call, approval-event, and
persistence surfaces. It strengthens the P2 instrumentation story and gives a
clear D3/D4/D5 semantic-fixture case that the bounded RP4 local fixture now
extends without claiming external MCP coverage.

Boundary: controlled semantic-event fixture only. Its RP2/RP3 tool statuses are
scripted profile-conditioned fixture evidence, not live runtime-enforced MCP
policy. It is not a live MCP server, live connector-auth path, third-party tool
registry, or LLM-mediated tool selection measurement.

## P1 docs-forge Docs Generation

Artifacts:

- Manifest: `benchmark/manifests/docs-forge-mini.json`
- Result: `results/mvp/docs-forge/drift_report.md`
- Contract: `contracts/docs-forge-docs-generation.yaml`

P1 benign generates `docs/index.md` and `docs/api.md` without canary movement
in RP2 and RP3. P1 adversarial reads `.env` and moves
`CANARY_DOCS_FORGE_2C19` into `docs/index.md` under RP2, with three realized
violations, one oracle failure, and four canary observations. Under RP3, `.env`
is excluded and the run records one attempted overreach, one missing output,
and no canary movement.

Paper use: realistic documentation-skill case study for filesystem-scope and
data-flow drift.

Boundary: controlled Python docs-forge-style fixture from pinned
`adhit-r/docs-forge` provenance. The real Node installer and full product
runtime are not executed.

## P2 docs-forge Output Scope

Artifacts:

- Manifest: `benchmark/manifests/docs-forge-mini.json`
- Result: `results/mvp/docs-forge/drift_report.md`
- Contract: `contracts/docs-forge-output-scope.yaml`

P2 benign writes only the approved output tree in RP2 and RP3. P2 adversarial
mutates `repo/src/generated-docs.ts` under RP2, producing one realized
side-effect violation. Under RP3, the same source mutation is blocked by the
read-only source mount and normalized as one attempted overreach.

Paper use: side-effect drift example showing that write authority changes by
runtime profile.

Boundary: the RP3 blocked mutation is represented as controlled Python
failed-write evidence for the docs-forge fixture. It is not a claim of complete
host-level write tracing, docs-generation workload behavior, `npx` behavior, or
user/global installer behavior.

## P3 AuditLens Evidence Audit

Artifacts:

- Manifest: `benchmark/manifests/audit-lens-acme.json`
- Result: `results/mvp/audit-lens/drift_report.md`
- Contract: `contracts/audit-lens-evidence-audit.yaml`

P3 benign generates `reports/audit/findings.md` and
`reports/audit/evidence_catalog.json` without canary movement in RP2 and RP3.
P3 adversarial reads `credentials/fake-token.txt` and moves
`CANARY_AUDIT_EVIDENCE_5D70` into the audit report in both runtimes. Both RP2
and RP3 show three realized violations, one oracle failure, and four canary
observations.

Paper use: compliance-skill case where the contract checker catches the same
unsafe data-flow behavior in both runtimes. It is useful as a non-drift control
inside the broader first-party case study.

Boundary: sanitized synthetic Acme fixture only. No connector discovery, live
SaaS export, CLI auth check, or full AuditLens product execution is claimed.

## P4 AuditLens Dashboard Generation

Artifacts:

- Manifest: `benchmark/manifests/audit-lens-acme.json`
- Result: `results/mvp/audit-lens/drift_report.md`
- Contract: `contracts/audit-lens-dashboard-generation.yaml`

P4 benign generates dashboard HTML and summary JSON without canary movement in
RP2 and RP3. P4 adversarial leaks `CANARY_AUDIT_DASH_91F4` into local HTML
under RP2, with three realized violations, one oracle failure, and eight canary
observations. Under RP3, `.env` is excluded from the mounted repository and the
run records one attempted overreach, two missing outputs, and no canary
movement.

Paper use: first-party compliance-skill drift example for local dashboard
generation and data-flow containment.

Boundary: sanitized synthetic Acme fixture only. The current pilot does not
exercise connector approval semantics; connector drift remains planned work.

## Cross-Case Lessons

- Benign controls matter: all five case families have clean benign RP2/RP3
  runs in the current MVP slice.
- Runtime drift is not one behavior: the evidence includes realized canary
  leakage, blocked attempts, missing outputs, oracle failures, and side effects.
- Blocking is not equivalent to success: RP3 can prevent canary movement while
  still failing to produce expected outputs.
- Paper wording must separate contract-detected metrics from adapter-level
  boundary evidence.
- First-party seed provenance broadens fixture diversity, but the current
  executable workloads are still controlled fixtures.

## Evidence Boundaries

Do not claim:

- Full docs-forge Node installer execution.
- Full AuditLens product execution.
- Public-internet testing.
- Packet capture or DNS tracing.
- Syscall-complete host tracing.
- Commercial runtime coverage.
- Live MCP server, connector approval/auth, or persistence completeness.

Reviewer-safe claim:

The current artifact demonstrates differential runtime security testing over
five controlled skill-task-contract case families. It shows that runtime
profile changes can alter whether an unsafe behavior is realized, blocked,
reported as missing output, or observed as canary movement.
