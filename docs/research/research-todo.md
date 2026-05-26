# SkillDiff Low-Level Research TODO

This TODO is the execution backlog for `docs/research/research-roadmap.md`.
It is the tracked steering list for the high-impact submission path. Older
root-level TODO files and ignored scratch strategy notes are non-authoritative.

Status values:

- `[ ]` not started
- `[~]` partially present or in progress
- `[x]` complete for the current evidence boundary

Current target order:

1. Runtime coverage before more isolated pilots.
2. Baselines and report cards before large benchmark scale.
3. Benchmark scale before prevalence-style claims.
4. Repeats, statistics, and adjudication before top-tier submission.
5. Artifact safety and anonymity before any external review package.

## S0: Steering And Claim Hygiene

Goal: keep the project pointed at runtime conformance rather than generic
agent-skill safety.

1. [x] Make `docs/research/research-roadmap.md` the high-level steering
   roadmap.
   Done when the roadmap states the primary contribution, venue path,
   evidence boundary, non-negotiable invariant, stop rules, and dependency
   order.
2. [x] Create this tracked low-level TODO under `docs/research/`.
   Done when low-level tasks map to the high-level steering phases.
3. [ ] Move any useful content from ignored scratch notes into tracked docs.
   Done when no active planning dependency exists only under ignored
   `research/` or root-level ignored TODO files.
4. [x] Update `paper/paper-spine.md` to use the title
   `SkillDiff: Differential Runtime Conformance Testing for Portable AI Agent
   Skills`.
   Done when paper title, abstract, RQs, and contributions consistently lead
   with runtime conformance.
5. [ ] Update `docs/research/related-work.md` with the newest crowded-field
   map.
   Include Semia, SkillSafetyBench, HarmfulSkillBench, RouteGuard,
   MCPShield, remote MCP authentication measurement, OWASP MCP Top 10, and
   OWASP Agentic Skills Top 10.
6. [ ] Add a claim-ledger entry for every new numerical steering claim that is
   promoted into paper-facing text.
   Done when `python3 tools/validate_claim_ledger.py` passes after the edit.

## S1: Make The Runtime Variable Unignorable

Goal: move from an RP2/RP3 pilot to a runtime-profile study.

### S1.1 Adapter Support Matrix

1. [x] Create `docs/research/adapter-support-matrix.md`.
   Include one row per runtime profile and columns for filesystem reads,
   filesystem writes, process/shell, network, activation, approval, tool/MCP,
   persistence, context inheritance, cleanup, and canary observation.
2. [x] Add support states for every surface.
   Use exactly: `implemented`, `simulated`, `fixture-only`, `unavailable`,
   `intentionally-unsupported`.
3. [x] Add an instrumentation-failure definition.
   Missing observer coverage must be counted separately from clean security
   behavior.
4. [x] Link the matrix from `docs/research/runtime-profiles-adapters.md` and
   `docs/research/research-roadmap.md`.

### S1.2 RP4 Bounded MCP-Connected Fixture

1. [x] Define a minimal bounded MCP fixture workspace under `benchmark/workspaces/`.
   It should include benign resource reads, allowed tool calls, denied tool
   discovery, denied auth checks, and canary-bearing tool-message attempts.
2. [x] Add or update an RP4 contract under `contracts/`.
   The contract must specify allowed tools, denied tools, approval-required
   tool calls, denied tool-message sinks, and expected outputs.
3. [x] Implement an RP4 runner in `tools/`.
   The runner must emit valid `activation.*`, `approval.*`, `tool.call` with
   MCP metadata, `persistence.*`, `capability.snapshot`, `run.start`, and
   `run.end` events where applicable. Literal `mcp.*` event types remain out
   of scope until the schema/checker stack is extended.
4. [x] Add expected-output metadata under `benchmark/expected/`.
   The expected output must distinguish task success from blocked unsafe
   behavior.
5. [x] Add a reproduction script under `experiments/`.
   It must validate traces, contract findings, and local-path hygiene.
6. [x] Add validator coverage to `scripts/verify_all.sh`.
   Done when `make verify` fails if RP4 trace or contract evidence is stale.
7. [x] Update `paper/method-boundaries.md`.
   State exactly which RP4 behaviors are live, fixture-level, or unsupported.

### S1.3 RP6 Hardened Runtime

1. [x] Define RP6 hardened policy knobs in `runtimes/profiles/RP6_policy_hardened.yaml`.
   Include filesystem read scope, write scope, network egress, shell/process,
   approval, tool/MCP availability, persistence, and cleanup behavior.
2. [x] Implement the RP6 adapter or policy wrapper.
   It must be able to run the current five case families without changing the
   skill, task, contract, workspace snapshot, prompt hash, variant, or repeat
   identity.
3. [x] Run RP6 over repo-audit, network-egress, MCP/tool workflow, AuditLens,
   and docs-forge.
   Current report card: `results/fixtures/rp6-policy-hardened/report_card.json`.
4. [x] Add RP2/RP3/RP6 comparison reports.
   Reports must separate realized violations, attempted overreach, missing
   outputs, task success, and canary observations. RP6-vs-RP2/RP3 pairs must
   stay labeled as mitigation report-card contrasts, not runtime-drift claims.
5. [x] Add RP6 results to the claim ledger only after validation passes.
   Claim boundary: RP6 is a current-case report-card pilot, excluded from the
   RP2/RP3 MVP aggregate counts. The report card includes one supplemental
   network-denial policy probe for direct blocked-connect/send evidence.
6. [x] Update `paper/tables/mvp-results.md` with RP6 strengthening evidence.
   Current table includes the report card, least-privilege baseline, minimal
   contrast, component-ablation report card, and repeat-stability artifact
   while keeping RP6 outside RP2/RP3 MVP counts.

### S1.4 RP1 And RP5 Coverage

1. [x] Decide whether RP1 is executable or explicitly simulated.
   Record the decision in the adapter support matrix.
   Current decision: RP1 is promoted as deterministic restricted-hosted
   simulator evidence only, not real hosted-provider behavior.
2. [x] If RP1 is simulated, implement a deterministic simulator that emits
   valid traces and marks unsupported surfaces clearly.
   Current artifacts: `src/skilldiff/adapters/restricted_hosted.py`,
   `tools/run_rp1_restricted_hosted_mvp.py`,
   `tools/validate_rp1_restricted_hosted_mvp.py`, and
   `results/fixtures/rp1-restricted-hosted/report_card.json`.
3. [x] Make RP5 plugin-style executable enough to measure install,
   activation, update, bundled-resource, and plugin metadata behavior.
   Current artifacts: `src/skilldiff/adapters/plugin_fixture.py`,
   `tools/run_rp5_plugin_fixture_mvp.py`,
   `tools/validate_rp5_plugin_fixture_mvp.py`, and
   `results/fixtures/rp5-plugin-style/report_card.json`.
   Boundary: fixture-backed only, not commercial plugin-store behavior.
4. [x] Add activation-negative-control tasks for RP5.
   Done when unrelated tasks produce `activation.not_selected` or equivalent
   non-activation evidence.
   Current negative-control case: `rp5-plugin-style.negative-control` records
   `activation.not_selected` with no shell execution, plugin storage write, or
   plugin activation.

## S2: Baselines And Runtime Report Cards

Goal: show why runtime conformance testing is not replaced by existing
scanner, least-privilege, or guardrail methods.

### S2.1 Runtime Report Cards

1. [x] Define `schemas/runtime_report_card.schema.json`.
   Include realized violations, attempted overreach, pairwise disagreements,
   missing outputs, benign task success, approval burden, utility cost,
   evidence coverage, and instrumentation failures.
2. [x] Add `src/skilldiff/reports/runtime_report_card.py`.
   It should consume contract findings and comparison JSON files.
3. [x] Add `tools/build_runtime_report_cards.py`.
   It should generate JSON and Markdown report cards for each runtime profile.
4. [x] Add report-card validation to `make verify`.
   Current check mode validates `results/derived/runtime-report-cards/`.
5. [~] Add a report-card table to the paper notes.
   The generated JSON/Markdown report cards exist for RP1, RP2, RP3, RP5, and
   RP6; manuscript table promotion remains open until final claim-ledger
   wording is frozen.

### S2.2 Static And Least-Privilege Baselines

1. [x] Add a static scanner baseline manifest.
   The baseline should classify skill text/scripts against the current attack
   family labels without using runtime traces.
   Current artifact: `results/fixtures/strengthening/static_scanner_baseline.json`.
2. [x] Add a Semia-style static reachability approximation where practical.
   If full Semia reproduction is out of scope, document the approximation and
   do not imply equivalence.
   Current artifact: `results/fixtures/strengthening/reachability_approximation.json`.
3. [x] Add a contract-derived least-privilege baseline.
   For each contract, derive minimum allowed reads, writes, network
   destinations, commands, tools, approvals, and sinks.
   Current artifact: `results/fixtures/strengthening/least_privilege_baseline.json`.
4. [x] Compare least-privilege baseline output against RP2/RP3/RP6 outcomes.
   Report where least privilege predicts overreach and where runtime behavior
   still differs.
   Current artifact: `results/fixtures/strengthening/rp6_mitigation_ladder.json`.
5. [x] Add ClawGuard/Task Shield-style action-boundary relevance checks for
   tool or command relevance.
   Treat this as a mitigation baseline, not as the main contribution.
   Current artifact: `results/fixtures/strengthening/action_boundary_baseline.json`.

### S2.3 Ablations

1. [x] Add toggles for filesystem read scope.
   Implemented as generated RP6 ablation profiles with `filesystem_read_scope`
   disabled.
2. [x] Add toggles for filesystem write scope.
   Implemented as generated RP6 ablation profiles with `filesystem_write_scope`
   disabled.
3. [x] Add toggles for network egress.
   Implemented as generated RP6 ablation profiles with
   `network_egress_blocker` disabled and a synthetic fake-sink response; no
   public internet claim is made.
4. [x] Add toggles for approval requirement.
   Implemented as generated RP6 ablation profiles with `approval_requirement`
   disabled.
5. [x] Add toggles for tool/MCP exposure.
   Implemented as generated RP6 ablation profiles with `semantic_tool_policy`
   disabled for controlled semantic fixture events.
6. [x] Add toggles for persistence/cache access.
   Implemented as generated RP6 ablation profiles with
   `persistence_cache_access` disabled. The runtime keeps the other RP6
   controls enabled and narrowly allows only contract persistence/cache path
   writes such as `./.skill-cache/**`; this remains file-backed fixture
   evidence, not a general hidden-persistence sandbox claim.
7. [x] Add an ablation report that shows security gain and utility cost.
   Current artifact: `results/fixtures/rp6-policy-hardened/ablations/component_report_card.json`.
   Boundary: this is bounded component-level fixture evidence, not product-scale
   defense causality.

## S3: Benchmark Expansion

Goal: reach a credible full-paper benchmark without diluting evidence quality.

### S3.1 Inclusion Checklist

1. [x] Create `schemas/benchmark_case.schema.json`.
   Required fields: skill ID, source, provenance level, execution level, task
   prompt path, task prompt hash, workspace snapshot hash, contract ID,
   expected-output path, canary labels, publication boundary, safety status,
   and category.
2. [x] Add `tools/validate_benchmark_cases.py`.
   It must fail on missing provenance, missing execution level, missing
   expected output, missing canary policy, or unsafe publication status.
3. [x] Add validation to `make verify`.
4. [x] Backfill the current case families into the new schema.
   Current artifact: `benchmark/manifests/benchmark-cases-current.json`.
   Current count: 20 skills / 60 skill-task-contract triples after promoting
   the planned synthetic inclusion entries to controlled single-repeat RP2/RP3
   fixture evidence. This is denominator and contract-check coverage only, not
   source-mix completion, repeat stability, prevalence evidence, live product
   behavior, or full-paper completion.
5. [x] Add a machine-readable benchmark scale-gap report.
   Current artifact: `results/derived/benchmark-scale-gap.json`.
   Current source-mix accounting uses skill-origin labels: 1 first-party,
   1 public, and 18 synthetic skills. It computes source-mix gaps but does not
   claim source-mix completion.

### S3.2 Category Expansion Targets

1. [~] Document automation: add at least two skills beyond docs-forge.
   Current status: two synthetic document-automation skills are now in the
   manifest with controlled single-repeat RP2/RP3 fixture traces.
2. [~] Repository maintenance: add at least three non-trivial repo workflows.
   Current status: three synthetic repository-maintenance skills are now in the
   manifest with controlled single-repeat RP2/RP3 fixture traces.
3. [~] Compliance/audit: add at least two workflows beyond AuditLens.
   Current status: two synthetic compliance/audit skills are now in the
   manifest with controlled single-repeat RP2/RP3 fixture traces.
4. [~] Data extraction: add tasks covering CSV, JSON, Markdown, and mixed
   file trees.
   Current status: one synthetic data-extraction fixture family contributes
   three tracked triples over CSV, JSON, and Markdown inputs, with controlled
   RP2/RP3 executable traces and zero runtime-drift findings. More public or
   first-party data-extraction skills are still needed for source-mix strength.
5. [~] API workflow: add mock API tasks covering credential exposure,
   no-egress policy, approval-required calls, and safe local fake sinks.
   Current status: two synthetic API workflow skills are now in the manifest
   with controlled single-repeat RP2/RP3 fixture traces.
6. [~] MCP/tool workflow: add at least two live or fixture-backed MCP/tool
   workflows beyond the current restricted-tool mini case.
   Current status: RP5 plugin-style fixture is backfilled as one additional
   synthetic fixture-backed MCP/tool workflow; one more remains for this
   category-expansion target.
7. [~] Local file operations: add path traversal, hidden write, cleanup, and
   cache-retention cases.
   Current status: one synthetic local-file-operation fixture family
   contributes output-only, archive-manifest, and cleanup-negative-control
   triples, with controlled RP2/RP3 executable traces and zero runtime-drift
   findings. One synthetic file-diff/local-operations skill adds path
   traversal and cache-retention coverage through the planned-entry promotion.

### S3.3 Scale Gates

1. [~] Reach 20 skills and 60 skill-task-contract triples before repeats.
   Current status: numeric 20/60 inventory floor is reached, with 44 formerly
   planned entries promoted to controlled single-repeat RP2/RP3 synthetic
   fixture evidence. It should not support prevalence, source-mix completion,
   repeat stability, live product behavior, or defense-success claims.
2. [ ] Reach 40 skills and 120 skill-task-contract triples before repeats.
   This is the minimum full-paper floor.
3. [~] Preserve a source mix: 8-10 first-party real skills, 15-20 public
   skills, and 12-15 controlled synthetic skills.
   Current status: explicit skill-origin source-mix labels are in the current
   manifest and derived scale-gap report. Current count is 1 first-party,
   1 public, and 18 synthetic skills; the mid-scale source-mix gap remains
   4 first-party and 7 public skills, so source-mix completion is blocked.
4. [ ] Add 1-2 adversarial variants per promoted base skill.
5. [ ] Store every prompt and expected output in tracked benchmark paths.
6. [ ] Keep full-product, controlled-fixture, and source-only evidence labels
   visible in every aggregate table.

## S4: Repeats, Statistics, And Adjudication

Goal: make the evaluation credible for a top-tier security review.

### S4.1 Repeat Runs

1. [ ] Add repeat ID support to all runners.
   Repeat ID must be emitted in `run.start`, contract findings, and
   comparison metadata.
2. [x] Add deterministic repeat commands for current controlled fixtures.
   Current artifact: `experiments/strengthening-evidence/reproduce_strengthening_evidence.sh`.
3. [ ] Run three repeats for every deterministic fixture promoted to main
   paper evidence.
   Current state: RP6 current-case strengthening fixtures now have repeat IDs
   1, 2, and 3 with bounded deterministic stability support. The 44
   planned-inclusion RP2/RP3 controlled fixtures also now have repeat IDs 1,
   2, and 3 under
   `results/fixtures/strengthening/rp2-rp3-repeat-stability/`, covering 264
   trace-valid observations and 132 same-repeat RP2/RP3 pairs. Remaining
   non-planned RP2/RP3 main benchmark repeat coverage and source-mix-backed
   repeat claims remain open.
4. [ ] Run five repeats for model-mediated or nondeterministic cases.
5. [ ] Report max-severity outcome alongside majority or median behavior.
   Do not average away realized high-severity violations.

### S4.2 Statistics

1. [x] Freeze inclusion/exclusion rules for descriptive rates.
   Current artifact: `benchmark/manifests/gate5-paper-inclusion.json`; it
   includes 60 current benchmark cases and excludes completed-statistics,
   reviewer-agreement, prevalence, source-mix-completion, and paper-grade
   completion claims.
2. [x] Add raw descriptive-rate artifact.
   Current artifact: `results/derived/gate5-descriptive-rates.json`; it
   reports 22 raw inventory and coverage rate records from the frozen inclusion
   table, without Wilson/bootstrap/McNemar, reviewer agreement, or prevalence
   claims.
3. [~] Add Wilson confidence intervals for simple rates.
   Current status: plan scaffold only in `paper/gate5-statistics-plan.md`;
   no intervals have been computed or claimed.
4. [ ] Add bootstrap intervals over skill-task-contract triples.
5. [ ] Add hierarchical bootstrap by skill when multiple tasks come from the
   same skill.
6. [x] Add paired runtime comparison summaries.
   Current artifact: `results/derived/paired-runtime-summary.json`; it is an
   aggregation layer for existing comparison artifacts, not Wilson/bootstrap
   statistics or reviewer-agreement evidence.
7. [ ] Use McNemar-style paired analysis only after the paired sample size is
   large enough.

### S4.3 Manual Review

1. [x] Add a manual adjudication form under `paper/` or `benchmark/review/`.
   Current artifact: `paper/gate5-adjudication-form.md`; it is a scaffold
   only and does not claim completed human review.
2. [x] Define labels for realized violation, attempted overreach,
   runtime-pair disagreement, missing output, oracle failure,
   instrumentation artifact, and non-claimable finding.
3. [x] Add a machine-readable manual review queue.
   Current artifact: `benchmark/review/gate5-review-queue.json`; it queues 60
   case-level review items from the frozen inclusion table, marks 50 as
   first-pass blinding eligible, and explicitly contains no completed reviews,
   reviewer IDs, agreement metrics, adjudication records, or statistics.
4. [x] Add a review-packet index with exact evidence refs.
   Current artifact: `benchmark/review/gate5-review-packet-index.json`; it
   creates 60 packet-index records, expands 50 mapped items to comparison,
   run, trace, and hash refs, and keeps 10 unmapped items blocked as
   metadata-only packets. It contains no raw trace content or completed review
   evidence.
5. [~] Blind runtime labels where possible for the first review pass.
   Current artifact: `benchmark/review/gate5-blinded-packet-bundle.json`; it
   exports 50 first-pass runtime-label-blinded pair-review packets from the
   mapped subset and leaves 10 unmapped packets blocked as metadata-only
   records. It is still pre-review and does not claim agreement,
   adjudication, statistics, prevalence, or paper-grade completion.
6. [ ] Run two-reviewer agreement on a representative sample.
   Current scaffold: `benchmark/review/gate5-review-export-templates.json`;
   it creates two blank reviewer templates over the same 50 blinded pair-review
   units. These templates do not count as completed human reviews and do not
   support agreement, adjudication, statistics, prevalence, or paper-grade
   completion claims.
7. [ ] Report percent agreement and Cohen's kappa where label counts support
   it.

## S5: Manuscript And Artifact Package

Goal: make the work submission-ready without unsupported claims.

### S5.1 Manuscript

1. [ ] Rewrite the introduction around the invariant:
   fixed skill/task/contract/workspace/prompt/variant/repeat, varied runtime.
2. [ ] Add a clear table separating current evidence, promoted evidence, and
   future work.
3. [ ] Add figures for architecture, trace lifecycle, runtime matrix, drift
   outcomes, report cards, and artifact flow.
4. [ ] Update related work with the crowded 2026 skill-security landscape.
5. [ ] Add reviewer-objection answers directly in the methodology and
   limitations sections.
6. [ ] Keep limitations explicit: no real secrets, no live SaaS exports, no
   public exfiltration, no commercial-runtime claims without evidence.

### S5.2 Safe Artifact Release

1. [x] Add `SECURITY.md`.
   Include safe disclosure, synthetic canary policy, no-real-secret policy,
   and public-internet boundary.
2. [x] Add `CITATION.cff`.
3. [x] Add benchmark data card.
4. [x] Add license clarity for benchmark fixtures, generated results,
   scripts, and first-party references.
5. [x] Add artifact anonymity checklist for double-blind venues.
6. [x] Add venue-specific AI-use disclosure draft.
7. [ ] Build a clean-checkout artifact bundle.
8. [ ] Ensure one documented command can reproduce the main paper tables.

### S5.3 Venue Gates

1. [ ] By 2026-06-15: RP4 fixture, RP6 current-case run, adapter matrix, and
   report-card schema exist.
2. [ ] By 2026-07-15: 20 skills, 60 triples, four profiles on promoted subset,
   first baselines, and repeat support exist.
3. [ ] By 2026-08-01: decide whether NDSS 2027 Fall is viable.
   Submit to NDSS only if 40 skills, 120 triples, four profiles, and writing
   are close enough to be credible.
4. [ ] By 2026-10-15: full benchmark, mitigation/report-card results,
   adjudication, and figures are complete for S&P decision.
5. [ ] By 2027-01-05: USENIX-ready manuscript and clean artifact package are
   complete.

## Immediate Next Step

S1.1, S1.2, S1.3, S1.4, the RP1 deterministic simulator slice, S2.1,
S2.2, the current least-privilege baseline, the S3.1 current-case manifest plus
scale-gap report, first data-extraction/local-file controlled RP2/RP3 coverage,
the 44-entry planned promotion, the planned-inclusion RP2/RP3 deterministic
repeat-stability strengthening artifact, the paired-runtime summary denominator
layer, the frozen Gate 5 inclusion table, and the raw descriptive-rate artifact
are complete for the bounded evidence boundary. The next dependency is moving
from bounded fixture stability toward source-mix-backed, repeat-backed, and
reviewer-adjudicated evidence:

1. Add public and additional first-party skills before claiming source-mix
   target completion.
2. Add repeat-run support to the remaining non-planned RP2/RP3 runners before
   promoting those cases into full-paper aggregate statistics.
3. Add manual review queue records and completed two-reviewer evidence before
   claiming reviewer agreement.
4. Keep Wilson/bootstrap/McNemar claims blocked until repeat-backed analysis
   and adjudication evidence exist.
5. Keep 40/120 unchecked until the manifest actually reaches that floor.
