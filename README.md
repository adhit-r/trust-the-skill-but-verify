# Trust the Skill, Verify the Runtime

`SkillDiff` is a research artifact for differential security testing of portable AI agent skills. The project holds the skill, task, security contract, workspace snapshot, task prompt, variant, and repeat identity fixed; varies the runtime profile; records normalized traces; and reports where runtime policy changes the observed security outcome.

The short version: a reusable agent skill is not secure or unsafe in isolation. Its effective behavior depends on the runtime that loads it: filesystem scope, shell access, network policy, approval prompts, tool exposure, persistence, credentials, and traceability.

![SkillDiff architecture](docs/assets/skilldiff-architecture.svg)

## What To Look At First

For a fast technical review:

1. Start with this README and the architecture diagrams below.
2. Run `make verify` to validate schemas, contracts, traces, result comparisons, claim ledger entries, and local-path hygiene.
3. Read `paper/tables/mvp-results.md` for the current result tables.
4. Read `paper/tables/evidence-boundary-matrix.md` before moving results into
   manuscript prose.
5. Read `paper/figures.md` before using manuscript figures or captions.
6. Read `paper/claim-ledger.md` before using any numeric claim.
7. Use `docs/research/` for method details instead of old root-level progress notes.

## Current Evidence Snapshot

These are feasibility and method claims, not ecosystem prevalence claims.

| Metric | Current value | Evidence |
| --- | ---: | --- |
| Controlled case families | 5 | `benchmark/manifests/skilldiff-mvp-baseline.json` |
| Paper-facing canonical trace files | 28 | `results/mvp/*/*_rp2_rp3_comparison.json` |
| Runtime-drift claims | 5 | `paper/tables/mvp-results.md` |
| Pairwise disagreements | 36 | `paper/tables/mvp-results.md` |
| Seeded real-source case families | 2 | AuditLens first-party; docs-forge pinned public-source |
| Controlled synthetic case families | 3 | repo-audit, network-egress, MCP/tool workflow |
| Current manifest inventory triples | 132 | `benchmark/manifests/benchmark-cases-current.json` |
| Current manifest source mix | 9 first-party / 17 public / 18 synthetic skills | `results/derived/benchmark-scale-gap.json` |
| Gate 5 descriptive denominator | 132 included cases / 22 raw rate records | `results/derived/gate5-descriptive-rates.json` |
| Gate 5 non-human interval artifact | 36 Wilson / 18 case-bootstrap / 6 hierarchical-bootstrap intervals; human review 0% | `results/derived/gate5-statistical-intervals.json` |
| Gate 5 manual review queue | 132 queued items / 122 blinding-eligible items | `benchmark/review/gate5-review-queue.json` |
| Gate 5 review-packet index | 132 packets / 122 comparison refs / 244 trace refs | `benchmark/review/gate5-review-packet-index.json` |
| Gate 5 blinded packet bundle | 122 blinded first-pass packet exports / 10 blocked metadata-only packets | `benchmark/review/gate5-blinded-packet-bundle.json` |
| Gate 5 review export templates | 2 blank reviewer templates / 122 assigned pair-review units each | `benchmark/review/gate5-review-export-templates.json` |
| Gate 5 human-review handoff | 2 reviewer slots / 122 pair-review units each / completed reviews 0 | `docs/research/gate5-human-review-handoff.json` |
| Submission readiness status | bounded non-human artifacts ready / human review 0% / final venue refresh open | `docs/research/submission-readiness-status.json` |
| Formerly planned entries promoted to controlled fixture evidence | 116 | `results/planned-inclusion/` |
| Planned-inclusion deterministic repeat observations | 696 | `results/fixtures/strengthening/rp2-rp3-repeat-stability/` |
| Current main deterministic repeat observations | 78 | `results/fixtures/strengthening/rp2-rp3-main-repeat-stability/` |

`results/derived/benchmark-scale-gap.json` computes source-mix gaps from
explicit manifest labels. After the planned 24-family source-mix expansion,
the manifest inventory is 44 skills and 132 triples with a 9 first-party / 17
public / 18 synthetic source mix. That closes the 40/120 numeric and
source-mix minimum gaps in manifest accounting only. These counts are manifest
and source-provenance accounting for the new entries. Seventy-two selected
source-mix cases now have controlled RP2/RP3 fixture evidence, and the current
source-mix metadata-only count is zero. Seventy-four first-party/public
source-mix cases across twenty-six families also have bounded deterministic RP6
repeat mitigation/report-card evidence. The inventory does not claim source-mix
evidence completion, adjudication, prevalence, defense success, or paper-grade
full-benchmark completion; source-mix completion remains blocked on
adjudication and any future task-specific real-run adapter that the safe
real-run promotion gate requires.

The 24 planned source-mix additions improve manifest coverage and source
labeling. Seventy-two selected cases across twenty-four source-mix families
have been promoted to controlled source-mix fixture evidence, covering benign,
boundary, and negative-control tasks. Seventy-four first-party/public cases now
also have bounded deterministic RP6 repeat mitigation/report-card evidence.
This remains bounded fixture/report-card evidence only; none of this claims
real product behavior, public-network behavior, commercial-runtime behavior,
prevalence, defense success, source-mix evidence completion, or human review.

The 116-entry promotion is controlled single-repeat RP2/RP3 fixture evidence.
It adds denominator and contract-check coverage only; it does not
claim live product behavior, public-network behavior, commercial-runtime
behavior, source-mix evidence completion, prevalence, or defense success.

The separate repeat-stability strengthening artifact runs those 116 controlled
fixtures across repeat IDs 1, 2, and 3 under RP2 and RP3. It supports bounded
deterministic fixture stability only, not statistical, prevalence,
reviewer-agreement, live-product, commercial-runtime, public-network, or
defense-success claims.

The current main RP2/RP3 repeat-stability artifact runs 13 controlled fixtures
across repeat IDs 1, 2, and 3. It supports bounded deterministic fixture
stability only and keeps statistical, prevalence, reviewer-agreement,
live-product, commercial-runtime, public-network, and defense-success claims
unsupported.

S1.2 also adds a bounded RP4 local MCP fixture under
`results/fixtures/rp4-mcp-connected/`. It validates MCP descriptor/resource/tool,
approval, blocked-attempt, canary, persistence, and cleanup event handling, but
it is excluded from the paper-facing MVP runtime-drift counts above.

![MVP result chart](docs/assets/mvp-results-chart.svg)

## Method

The core unit is a skill-task-contract triple:

```text
(skill_id, task_id, contract_id)
```

The harness executes that triple under runtime profiles such as RP2 local coding agent and RP3 Docker sandbox, then normalizes evidence into `trace.jsonl`. Contract checking separates:

| Outcome | Meaning |
| --- | --- |
| Realized contract violation | A denied event completes, exposes data, persists state, transmits data, or produces a forbidden side effect. |
| Attempted overreach | A denied action is attempted but blocked, denied, or fails before exposure or side effect. |
| Runtime-pair disagreement | Two runtime profiles produce different security-relevant traces for the same skill-task-contract triple. |

![Runtime comparison flow](docs/assets/runtime-comparison-flow.svg)

## Repository Map

| Path | Purpose |
| --- | --- |
| `src/skilldiff/` | Core trace, adapter, contract, metric, and report helpers. |
| `tools/` | Repo-local validators and experiment runners. |
| `schemas/` | JSON schemas for traces, runtime profiles, and security contracts. |
| `runtimes/profiles/` | RP1-RP6 runtime profile definitions. |
| `contracts/` | Task-conditioned security contracts used by the checker. |
| `benchmark/` | Manifests, tasks, expected outputs, and controlled workspaces. |
| `experiments/` | Reproduction scripts for each case family. |
| `results/mvp/` | Canonical paper-facing result comparisons and drift reports. |
| `results/planned-inclusion/` | Controlled single-repeat fixture evidence for formerly planned benchmark entries. |
| `results/fixtures/` | Supplemental bounded fixture/report-card evidence excluded from RP2/RP3 MVP aggregate counts. |
| `results/live/` | Bounded live-installer scaffold evidence. |
| `results/raw/` | Raw local run artifacts and trace files; generated sidecars and scratch workspaces are ignored. |
| `paper/` | Paper-facing claim ledger, protocol, case-study notes, and result tables. |
| `paper/figures/` | Canonical SVG figure package and figure manifest for the manuscript. |
| `docs/research/` | Stable research notes moved out of the repository root. |
| `docs/assets/` | Rendered diagrams used by this README. |

## Quick Start

Use Python 3.11 or newer. Docker is required for RP3 live runs and for reproducing Docker-backed evidence.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
PYTHON_BIN=.venv/bin/python make verify
```

Generate a small Markdown report for one trace:

```bash
PYTHON_BIN=.venv/bin/python \
  .venv/bin/python tools/skilldiff.py report \
  results/raw/rp2-abf6e88e54d0/trace.jsonl
```

Run one reproduction script:

```bash
PYTHON_BIN=.venv/bin/python \
  bash experiments/repo-audit-mvp/reproduce_repo_audit_mvp.sh
```

## Research Notes

The stable research notes are organized under `docs/research/`:

| Document | Use |
| --- | --- |
| `docs/research/research-roadmap.md` | Problem statement, thesis, positioning, and roadmap. |
| `docs/research/research-todo.md` | Current low-level steering TODO mapped to the roadmap phases. |
| `docs/research/adapter-support-matrix.md` | Current per-runtime, per-surface evidence support matrix. |
| `docs/research/drift-taxonomy-metrics.md` | D1-D5 drift taxonomy and measurement rules. |
| `docs/research/security-contract-model.md` | Task-conditioned contract model. |
| `docs/research/runtime-profiles-adapters.md` | Runtime-profile and adapter semantics. |
| `docs/research/trace-harness.md` | Trace-harness boundary and raw evidence layout. |
| `docs/research/related-work.md` | Differentiation from skill scanners, least privilege, MCP security, and supply-chain work. |

Use `docs/research/research-roadmap.md` and `docs/research/research-todo.md`
as the steering pair. Older scratch notes, root-level TODO files, and private
research strategy drafts are ignored so the public repository stays reviewable.

## Evidence Boundary

This repository uses synthetic canaries only. The current baseline does not claim:

- ecosystem prevalence,
- commercial-runtime coverage,
- public-internet testing,
- packet capture or syscall-complete host tracing,
- full product execution for docs-forge or AuditLens,
- live MCP connector authorization coverage.
- external MCP server or commercial MCP-client behavior from the RP4 fixture.

Any paper text that introduces or changes a number should update `paper/claim-ledger.json` and pass:

```bash
PYTHON_BIN=.venv/bin/python make verify
```
