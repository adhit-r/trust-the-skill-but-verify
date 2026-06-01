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

## Current Non-Human Full-Paper TODO Snapshot

This section is the short execution checklist for the remaining non-human work
after the Gate 5 review-infrastructure branch. Human/manual review is tracked
separately under S4.3 and is intentionally excluded from this snapshot.

1. [x] Clear GitHub CI and merge the Gate 5 review-infrastructure PR.
   GitHub `make verify` passed on `codex/gate5-review-infra` in PR #1 on
   2026-05-31, local clean-checkout verification passed, and the squash merge
   to `main` passed the post-merge `make verify` run. GitGuardian and SafeDep
   did not report a vulnerability; both were limited by the very large PR diff.
   A compensating dependency/workflow review found no changes to dependency
   manifests, lockfiles, Dockerfiles, or GitHub workflow files in the squash
   merge.
2. [x] Scale past the 40 skills / 120 triples manifest floor.
   The planned 24-family source-mix expansion is now in the manifest, moving
   the inventory to 44 skills and 132 tracked skill-task-contract triples.
   Treat this as manifest/source-provenance accounting for the new entries.
   Seventy-two selected source-mix cases now have controlled RP2/RP3 fixture
   evidence across twenty-four first-party/public families, and the current
   source-mix metadata-only count is zero. Seventy-four first-party/public
   source-mix cases across twenty-six families also have bounded RP6
   mitigation/report-card evidence and three-repeat deterministic
   source-mix RP6 stability evidence. Paper-grade completion still requires
   adjudication evidence and safe task-specific real-run adapters where
   appropriate. Current bounded partial-real slice:
   `results/live/ripgrep-public-local-binary/live_local_binary_search_result.json`
   (local real ripgrep binary over synthetic allowlisted workspace only).
3. [x] Keep the source-mix gap explicit before calling the benchmark
   full-paper credible.
   Current post-expansion mix is 9 first-party, 17 public, and 18 synthetic
   skills. That closes the full-paper source-mix minimum gap in manifest
   accounting only; bounded source-mix RP6 report-card evidence and
   repeat-backed deterministic source-mix RP6 evidence now exist, but
   source-mix evidence completion remains blocked until adjudication evidence
   and safe task-specific real-run adapters exist.
4. [x] Finish repeat and statistics infrastructure beyond the bounded fixture
   slices.
   Current main RP2/RP3 controlled fixtures now have a bounded deterministic
   repeat-stability artifact with 13 cases, 78 trace-valid observations, and
   39 same-repeat RP2/RP3 pairs. First-party/public source-mix RP6
   report-card fixtures now have a bounded deterministic repeat-stability
   artifact with 74 cases and 222 trace-valid observations. The Gate 5
   machine-only interval artifact reports Wilson, case-bootstrap, and
   hierarchical-bootstrap intervals, plus max severity beside majority/median
   paired-runtime behavior. Current model-mediated/nondeterministic benchmark
   case count is zero; future admitted cases remain blocked until five-repeat
   evidence exists. McNemar-style paired analysis remains blocked until binary
   matched outcome labels support it. Current guardrails:
   `tools/validate_repeat_coverage.py` validates the repeat-backed buckets,
   and `tools/validate_runner_repeat_hygiene.py` blocks runner wrappers that
   collapse future runs back to repeat ID 1.
5. [x] Promote runtime report cards and evidence-boundary tables into the
   manuscript.
   Current artifact: `paper/tables/evidence-boundary-matrix.md`; it separates
   current evidence, promoted bounded evidence, review-ready scaffolds, and
   future work, while keeping simulator, fixture, source-only, report-card,
   repeat, machine-only interval, and human-review boundaries visible.
6. [x] Rewrite the manuscript introduction around the invariant.
   Current artifact: `paper/introduction-skeleton.md`; it now states the
   fixed skill, task, contract, workspace snapshot, prompt, variant, and repeat
   invariant; identifies runtime profile as the variable; and keeps measured
   conformance changes separate from prevalence, commercial-runtime,
   public-internet, defense-success, and completed-human-review claims.
7. [x] Add the core paper figures.
   Current artifacts: `paper/figures/` and `paper/figures.md`; the package
   includes architecture, trace lifecycle, runtime matrix, drift outcomes,
   runtime report cards, and artifact flow figures, with a manifest and
   validator-backed boundaries for simulator, fixture, report-card,
   machine-only interval, release-bundle, and human-review claims.
8. [x] Refresh related work with current primary sources before any
   submission-facing claim.
   Current artifact: `docs/research/related-work.md`; primary-source map
   refreshed on 2026-05-28. It covers Semia, SkillSafetyBench,
   HarmfulSkillBench, RouteGuard, MCPShield, remote MCP authentication
   measurement, OWASP MCP Top 10, and OWASP Agentic Skills Top 10 while
   avoiding firstness, prevalence, Semia-equivalence, live-guardrail,
   completed-human-review, commercial-runtime, public-network, and
   defense-success claims.
9. [x] Build the clean artifact-release bundle.
   Current artifacts: `scripts/reproduce_paper_tables.sh`,
   `tools/build_artifact_release_bundle.py`, and
   `tools/validate_artifact_release_bundle.py`; the path is a curated local
   machine-only bundle, not a whole-repo archive, public release, external
   review packet, or completed human-review artifact. Raw stdout/stderr,
   workspace directories, raw traces, secrets, auth state, cookies, and local
   scratch stay outside the release boundary.
10. [x] Keep the claim ledger synchronized with every paper-facing number.
    Current validation: `python3 tools/validate_claim_ledger.py` passes after
    the related-work and artifact-release updates.
11. [x] Add a machine-readable submission-readiness status.
    Current artifact: `docs/research/submission-readiness-status.json`; it
    records bounded non-human artifacts as ready for the current claim boundary
    while keeping human review at 0%, final selected-venue policy refresh open,
    and paper-grade submission readiness unsupported.
12. [x] Add a machine-readable human-review handoff gate.
    Current artifact: `docs/research/gate5-human-review-handoff.json`; it
    records the exact Gate 5 reviewer inputs, two reviewer slots, completed
    export validator command, and no-completed-review boundary before any real
    reviewer agreement or adjudication claim.
13. [x] Add a machine-readable selected-venue policy source audit.
    Current artifact: `docs/artifact/selected-venue-policy-source-audit.json`;
    it records seven official venue/policy sources checked for the USENIX
    Security 2027 target and top-tier backplan while keeping final CFP/CFA
    freeze, external submission, public release, and paper-grade readiness
    unclaimed.

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
3. [x] Move any useful content from ignored scratch notes into tracked docs.
   Current clean-checkout state has no ignored active roadmap/TODO dependency
   under `research/` or root-level scratch planning files. The tracked steering
   pair remains `docs/research/research-roadmap.md` plus this TODO.
4. [x] Update `paper/paper-spine.md` to use the title
   `SkillDiff: Differential Runtime Conformance Testing for Portable AI Agent
   Skills`.
   Done when paper title, abstract, RQs, and contributions consistently lead
   with runtime conformance.
5. [x] Update `docs/research/related-work.md` with the newest crowded-field
   map.
   Current artifact: `docs/research/related-work.md`; source check completed
   on 2026-05-28 against current primary arXiv, MCP, and OWASP sources.
6. [x] Add a claim-ledger entry for every new numerical steering claim that is
   promoted into paper-facing text.
   Current validation: `python3 tools/validate_claim_ledger.py` passes after
   the Gate 5, artifact-release, and CI-warning cleanup updates. This remains
   an ongoing guardrail: any newly promoted number must either reuse an
   existing ledger claim or add a new one before merge.

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
5. [x] Add a report-card table to the paper notes.
   Current artifact: `paper/tables/runtime-report-card-summary.md`; it is
   generated from `results/derived/runtime-report-cards/*_report_card.json`
   and checked by `make verify`, preserving simulator, fixture,
   mitigation/report-card, no-commercial-runtime, no-defense-success,
   no-prevalence, and no-completed-human-review boundaries.

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
   Current count: 44 skills / 132 skill-task-contract triples after the
   planned 24-family first-party/public source-mix manifest expansion and the
   earlier promoted synthetic inclusion entries. The 24-family source-mix
   slice now includes seventy-two selected controlled RP2/RP3 fixture cases, and
   the current source-mix metadata-only count is zero. Seventy-four
   first-party/public source-mix cases now also have bounded RP6
   mitigation/report-card evidence. Together they support denominator,
   contract-check, and bounded report-card coverage only, not source-mix
   evidence completion, prevalence evidence, runtime-drift findings, live
   product behavior, or full-paper completion.
5. [x] Add a machine-readable benchmark scale-gap report.
   Current artifact: `results/derived/benchmark-scale-gap.json`.
   Current source-mix accounting uses skill-origin labels: 9 first-party,
   17 public, and 18 synthetic skills after the planned source-mix expansion.
   It computes source-mix gaps but does not claim source-mix evidence
   completion.

### S3.2 Category Expansion Targets

1. [x] Document automation: add at least two skills beyond docs-forge.
   Current manifest category count: 21 document-automation triples, with
   bounded controlled-fixture labels preserved.
2. [x] Repository maintenance: add at least three non-trivial repo workflows.
   Current manifest category count: 21 repository-maintenance triples, with
   controlled RP2/RP3 fixture evidence for promoted entries.
3. [x] Compliance/audit: add at least two workflows beyond AuditLens.
   Current manifest category count: 15 compliance/audit triples, with
   controlled-fixture and first-party/public source-mix boundaries preserved.
4. [x] Data extraction: add tasks covering CSV, JSON, Markdown, and mixed
   file trees.
   Current manifest category count: 21 data-extraction triples. Category
   coverage is complete for the manifest floor; paper-grade evidence still
   depends on adjudication and any later safe task-specific real-run promotion.
5. [x] API workflow: add mock API tasks covering credential exposure,
   no-egress policy, approval-required calls, and safe local fake sinks.
   Current manifest category count: 18 API-workflow triples, with local
   fake-sink and no-public-exfiltration boundaries preserved.
6. [x] MCP/tool workflow: add at least two live or fixture-backed MCP/tool
   workflows beyond the current restricted-tool mini case.
   Current manifest category count: 18 MCP/tool-workflow triples, including
   bounded RP4/RP5 and public/first-party source-mix entries. This remains
   fixture/source-mix evidence, not external MCP-server behavior.
7. [x] Local file operations: add path traversal, hidden write, cleanup, and
   cache-retention cases.
   Current manifest category count: 18 local-file-operation triples, with
   path-traversal, cleanup, output-only, and cache-retention coverage kept
   under bounded fixture labels.

### S3.3 Scale Gates

1. [x] Reach 20 skills and 60 skill-task-contract triples before repeats.
   Current status: superseded by the 44 skills / 132 triples manifest floor,
   with 116 formerly planned entries promoted to controlled single-repeat
   RP2/RP3 fixture evidence. It still does not support prevalence,
   source-mix evidence completion, live product behavior, or defense-success
   claims.
2. [x] Reach 40 skills and 120 skill-task-contract triples before repeats.
   Current status: the manifest/source-provenance inventory reaches 44 skills
   and 132 triples. This closes the numeric floor only, not executable
   full-paper evidence.
3. [x] Preserve a source mix with additional first-party and public coverage,
   without expanding synthetic coverage further for the current gap.
   Current status: explicit skill-origin source-mix labels are in the current
   manifest and derived scale-gap report. Post-expansion count is 9
   first-party, 17 public, and 18 synthetic skills; the remaining full-paper
   source-mix gap is zero in manifest accounting, and all current source-mix
   planned cases have controlled RP2/RP3 fixture evidence. Seventy-four
   first-party/public cases also have bounded RP6 mitigation/report-card
   evidence and three-repeat deterministic RP6 stability evidence. Source-mix
   evidence completion remains blocked until adjudication evidence and safe
   task-specific real-run adapters exist.
4. [~] Add 1-2 adversarial variants per promoted base skill.
   Current status: every one of the 44 promoted skills contributes exactly
   three tracked triples, and most promoted triples include explicit boundary,
   adversarial, unauthorized, or negative-control cases. Keep this partial
   until stricter per-skill variant labels are machine-checked rather than
   inferred from case names.
5. [x] Store every prompt and expected output in tracked benchmark paths.
   Current manifest status: all 132 cases have tracked prompt refs and
   expected-output oracle refs. The former four unresolved refs now point to
   bounded oracle metadata for the network-egress MVP fake-sink smoke case and
   the three RP5 plugin-style report-card cases. This closes the steering
   blocker only; it does not promote public-network, commercial-runtime,
   prevalence, defense-success, or paper-grade completion claims
   (`CL-STEER-001`).
6. [x] Keep full-product, controlled-fixture, and source-only evidence labels
   visible in every aggregate table.
   Current status: manifest provenance, execution-level, publication-boundary,
   report-card, scale-gap, inclusion, and evidence-boundary artifacts preserve
   controlled-fixture, source-mix, simulator, report-card, and future-work
   labels.

## S4: Repeats, Statistics, And Adjudication

Goal: make the evaluation credible for a top-tier security review.

### S4.1 Repeat Runs

1. [x] Add repeat ID support to all runners.
   The remaining runner wrappers now expose caller-provided `--repeat-id`
   plumbing, live trace builders stamp the caller repeat into `run.start`, and
   generated findings/comparisons keep repeat IDs through the existing
   contract checker and comparison invariants. `tools/validate_runner_repeat_hygiene.py`
   is wired into `scripts/verify_all.sh` to block wrapper regressions.
2. [x] Add deterministic repeat commands for current controlled fixtures.
   Current artifact: `experiments/strengthening-evidence/reproduce_strengthening_evidence.sh`.
3. [x] Run three repeats for every deterministic fixture promoted to main
   paper evidence.
   Current state: RP6 current-case strengthening fixtures now have repeat IDs
   1, 2, and 3 with bounded deterministic stability support. The 116
   planned-inclusion RP2/RP3 controlled fixtures also now have repeat IDs 1,
   2, and 3 under
   `results/fixtures/strengthening/rp2-rp3-repeat-stability/`, covering 696
   trace-valid observations and 348 same-repeat RP2/RP3 pairs. The 13 current
   non-planned main RP2/RP3 controlled fixtures now have repeat IDs 1, 2, and
   3 under
   `results/fixtures/strengthening/rp2-rp3-main-repeat-stability/`, covering
   78 trace-valid observations and 39 same-repeat RP2/RP3 pairs. The
   first-party/public source-mix RP6 report-card fixtures now have repeat IDs
   1, 2, and 3 under
   `results/fixtures/strengthening/source-mix-rp6-repeat-stability/`,
   covering 222 trace-valid observations across 74 cases. The repeat-coverage
   validator blocks accidental promotion of RP1/RP5 report-card evidence,
   model-mediated cases, or future metadata-only source-mix entries into
   repeat-backed aggregate claims.
4. [x] Run five repeats for model-mediated or nondeterministic cases.
   Current manifest state: no model-mediated or nondeterministic benchmark
   cases are admitted into repeat-backed claims. `tools/validate_repeat_coverage.py`
   blocks any future admitted model-mediated/nondeterministic case until
   five-repeat evidence and matching validators exist.
5. [x] Report max-severity outcome alongside majority or median behavior.
   Current artifact: `results/derived/gate5-statistical-intervals.json`
   reports max pair severity beside majority pair classification and median
   disagreement count, with an explicit non-human-adjudicated severity
   boundary.

### S4.2 Statistics

1. [x] Freeze inclusion/exclusion rules for descriptive rates.
   Current artifact: `benchmark/manifests/gate5-paper-inclusion.json`; it
   includes 132 current benchmark cases and excludes completed-statistics,
   reviewer-agreement, prevalence, source-mix-completion, and paper-grade
   completion claims.
2. [x] Add raw descriptive-rate artifact.
   Current artifact: `results/derived/gate5-descriptive-rates.json`; it
   reports 22 raw inventory and coverage rate records from the frozen inclusion
   table, without Wilson/bootstrap/McNemar, reviewer agreement, or prevalence
   claims.
3. [x] Add Wilson confidence intervals for simple rates.
   Current artifact: `results/derived/gate5-statistical-intervals.json`; it
   reports 36 Wilson intervals over the frozen descriptive and paired-runtime
   denominators, without prevalence, human-review, adjudication, or
   hypothesis-test claims.
4. [x] Add bootstrap intervals over skill-task-contract triples.
   Current artifact: `results/derived/gate5-statistical-intervals.json`; it
   reports 18 nonparametric case-bootstrap intervals with fixed seed and
   sample count.
5. [x] Add hierarchical bootstrap by skill when multiple tasks come from the
   same skill.
   Current artifact: `results/derived/gate5-statistical-intervals.json`; it
   reports 6 hierarchical skill/case bootstrap intervals.
6. [x] Add paired runtime comparison summaries.
   Current artifact: `results/derived/paired-runtime-summary.json`; it is an
   aggregation layer for existing comparison artifacts. The interval artifact
   now reports max severity beside majority and median paired-runtime behavior,
   while keeping human adjudication unsupported.
7. [x] Use McNemar-style paired analysis only after the paired sample size is
   large enough.
   Current status: explicitly deferred in
   `results/derived/gate5-statistical-intervals.json` because the present
   paired records are comparator classifications and finding-set deltas, not a
   frozen binary human-adjudicated matched outcome table.

### S4.3 Manual Review

1. [x] Add a manual adjudication form under `paper/` or `benchmark/review/`.
   Current artifact: `paper/gate5-adjudication-form.md`; it is a scaffold
   only and does not claim completed human review.
2. [x] Define labels for realized violation, attempted overreach,
   runtime-pair disagreement, missing output, oracle failure,
   instrumentation artifact, and non-claimable finding.
3. [x] Add a machine-readable manual review queue.
   Current artifact: `benchmark/review/gate5-review-queue.json`; it queues 132
   case-level review items from the frozen inclusion table, marks 122 as
   first-pass blinding eligible and 10 as metadata-only unmapped, and
   explicitly contains no completed reviews, reviewer IDs, agreement metrics,
   adjudication records, or statistics.
4. [x] Add a review-packet index with exact evidence refs.
   Current artifact: `benchmark/review/gate5-review-packet-index.json`; it
   creates 132 packet-index records, expands 122 mapped items to comparison,
   run, trace, and hash refs, and keeps 10 unmapped items blocked as
   metadata-only packets. It contains no raw trace content or completed review
   evidence.
5. [x] Blind runtime labels where possible for the first review pass.
   Current artifact: `benchmark/review/gate5-blinded-packet-bundle.json`; it
   exports 122 first-pass runtime-label-blinded pair-review packets from the
   mapped subset and leaves 10 unmapped packets blocked as metadata-only
   records. It is still pre-review and does not claim agreement,
   adjudication, statistics, prevalence, or paper-grade completion.
6. [ ] Run two-reviewer agreement on a representative sample.
   Current scaffold: `benchmark/review/gate5-review-export-templates.json`;
   it creates two blank reviewer templates over the same 122 blinded pair-review
   units. These templates do not count as completed human reviews and do not
   support agreement, adjudication, statistics, prevalence, or paper-grade
   completion claims.
7. [ ] Report percent agreement and Cohen's kappa where label counts support
   it.

## S5: Manuscript And Artifact Package

Goal: make the work submission-ready without unsupported claims.

### S5.1 Manuscript

1. [x] Rewrite the introduction around the invariant:
   fixed skill/task/contract/workspace/prompt/variant/repeat, varied runtime.
   Current artifact: `paper/introduction-skeleton.md`; validated by
   `CL-P1-003`.
2. [x] Add a clear table separating current evidence, promoted evidence, and
   future work.
   Current artifact: `paper/tables/evidence-boundary-matrix.md`.
3. [x] Add figures for architecture, trace lifecycle, runtime matrix, drift
   outcomes, report cards, and artifact flow.
   Current artifacts: `paper/figures/` and `paper/figures.md`; validated by
   `tools/validate_paper_figures.py` and `CL-P1-004`.
4. [x] Update related work with the crowded 2026 skill-security landscape.
   Current artifact: `docs/research/related-work.md`; it keeps the paper's
   positioning as runtime conformance under a fixed invariant rather than a
   scanner, harmful-skill corpus, least-privilege compiler, or MCP-only
   defense.
5. [x] Add reviewer-objection answers directly in the methodology and
   limitations sections.
   Current artifact: `paper/method-boundaries.md`; it now includes
   reviewer-safe answers for benchmark novelty, evidence scale, artificial
   profiles, instrumentation gaps, mitigation claims, review scaffolds, and
   local artifact-release boundaries.
6. [x] Keep limitations explicit: no real secrets, no live SaaS exports, no
   public exfiltration, no commercial-runtime claims without evidence.
   Current validation: `tools/validate_paper_claim_boundaries.py` is wired into
   `make verify` to check high-risk boundary phrases and stale status rows.

### S5.2 Safe Artifact Release

1. [x] Add `SECURITY.md`.
   Include safe disclosure, synthetic canary policy, no-real-secret policy,
   and public-internet boundary.
2. [x] Add `CITATION.cff`.
   Current metadata points to the repository URL and intentionally omits the
   optional CFF `license` field; `tools/validate_artifact_metadata.py` verifies
   that the documented `NOASSERTION` boundary is not a placeholder.
3. [x] Add benchmark data card.
4. [x] Add license clarity for benchmark fixtures, generated results,
   scripts, and first-party references.
5. [x] Add artifact anonymity checklist for double-blind venues.
6. [x] Add venue-specific AI-use disclosure draft.
7. [x] Build a clean-checkout artifact bundle.
   Current machine-only local path:
   `tools/build_artifact_release_bundle.py` plus
   `tools/validate_artifact_release_bundle.py`. This remains a curated local
   bundle and does not claim public release or external review readiness.
8. [x] Ensure one documented command can reproduce the main paper tables.
   Current command: `PYTHON_BIN=python3 make reproduce-paper-tables`, with
   `ARTIFACT_OUTPUT_ROOT` support for non-destructive validation.

### S5.3 Venue Gates

1. [x] By 2026-06-15: RP4 fixture, RP6 current-case run, adapter matrix, and
   report-card schema exist.
   Completed ahead of date on the verified main branch.
2. [x] By 2026-07-15: 44 skills, 132 triples, four profiles on the promoted
   subset, first baselines, and repeat support exist, with the 24-family
   source-mix expansion promoted to controlled fixture evidence while preserving
   bounded evidence labels.
   Completed ahead of date on the verified main branch; this is still bounded
   evidence, not paper-grade completion.
3. [ ] By 2026-08-01: decide whether NDSS 2027 Fall is viable.
   Submit to NDSS only if 40 skills, 120 triples, four profiles, and writing
   are close enough to be credible.
4. [~] By 2026-10-15: full benchmark, mitigation/report-card results,
   adjudication, and figures are complete for S&P decision.
   Machine artifacts, figures, report cards, intervals, and release-bundle
   scaffolds are present; adjudication remains the blocking dependency.
5. [~] By 2027-01-05: USENIX-ready manuscript and clean artifact package are
   complete.
   The clean artifact path and claim-boundary checks are present; the
   manuscript is still not USENIX-ready until adjudication and final
   selected-venue policy refresh are complete.

## Immediate Next Step

S1.1, S1.2, S1.3, S1.4, the RP1 deterministic simulator slice, S2.1,
S2.2, the current least-privilege baseline, the S3.1 current-case manifest plus
scale-gap report, first data-extraction/local-file controlled RP2/RP3 coverage,
the 116-entry planned promotion, the planned-inclusion RP2/RP3 deterministic
repeat-stability strengthening artifact, the paired-runtime summary denominator
layer, the frozen Gate 5 inclusion table, the raw descriptive-rate artifact,
the Gate 5 non-human interval artifact, the 44/132
manifest/source-provenance floor, the first-party/public source-mix RP6
report-card slice, its three-repeat deterministic stability artifact, and the
clean local release-bundle path, citation metadata, and explicit license
boundary, plus the selected packaging-profile pass for `anonymous_review` and
`public_archive` candidate metadata, plus the selected-venue policy snapshot
for USENIX Security 2027 Cycle 2, plus the selected-venue policy source audit,
plus the safe real-run promotion decision gate, plus the human-review handoff
gate, plus the submission-readiness status gate, are complete for the bounded
non-human evidence boundary.
Status shorthand: bounded non-human evidence boundary is complete.

The remaining submission-readiness dependencies are:

1. Run the two-reviewer workflow from the existing blinded packet templates
   before claiming reviewer agreement, adjudication, or human-reviewed
   statistics.
2. Keep McNemar, reviewer-agreement, and adjudication claims blocked until
   binary matched outcome labels and real two-reviewer evidence exist.
3. Refresh the selected-venue policy snapshot against the final 2027 CFP/CFA
   before external artifact submission. The repo now validates the current
   official-source snapshot and source audit, `anonymous_review` review
   metadata, and `public_archive` post-acceptance metadata, but actual
   submission packaging still has to follow the selected venue's current rules.
4. Add new safe real-run adapters only if they close a named paper gap under
   `docs/research/safe-real-run-promotion-decisions.json`; do not treat them
   as required for the current bounded non-human completion state.
