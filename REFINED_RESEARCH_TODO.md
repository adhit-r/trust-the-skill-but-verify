# Refined Research TODO

This TODO is mapped to `REFINED_RESEARCH_ROADMAP.md`. Status values:

- `[ ]` not started
- `[~]` in progress or partially present
- `[x]` complete in the current repo

## P0: Evidence Integrity Gate

1. [~] Add source-provenance hash verification to
   `experiments/audit-lens-mvp/reproduce_audit_lens_mvp.sh`.
   Current state: the script verifies the committed fixture workspace snapshot
   before Docker execution, and verifies the external pinned source checkout
   when `AUDIT_LENS_SOURCE_ROOT` is supplied. Full done still requires a
   published pinned-source hash list for AuditLens.
2. [~] Add source-provenance hash verification to
   `experiments/docs-forge-mvp/reproduce_docs_forge_mvp.sh`.
   Current state: the script verifies the committed fixture workspace snapshot
   before Docker execution, and verifies the external pinned source commit,
   tree, and listed source blob hashes when `DOCS_FORGE_SOURCE_ROOT` is
   supplied.
3. [x] Add a repo-wide path-scrub validation command.
   Done when CI fails if tracked publishable artifacts contain local paths such
   as `<LOCAL_HOME>`.
4. [x] Integrate path scrubbing into reproduction output generation.
   Done: AuditLens, docs-forge, repo-audit, and network-egress reproduction
   scripts scrub generated raw/result artifacts after validation.
5. [x] Make contract evidence resolution artifact-root-aware.
   Done: scrubbed `<REPO_ROOT>` evidence references are resolved through
   `tools/check_contract.py --artifact-root`, which defaults to the checkout
   root for clean artifact rechecks.
6. [~] Strengthen `compare_contract_runs` invariants.
   Current state: pairwise drift classification requires matching available
   skill ID, task ID, contract ID, and repeat ID from trace-start context.
   Prompt hash, workspace snapshot hash, and variant ID are reported as
   unchecked planned invariants until runners emit them.
7. [x] Normalize RP3 blocked source mutation as an attempted write event.
   Done: docs-forge P2 RP3 emits a failed `filesystem.write` event for
   `./repo/src/generated-docs.ts`, and the contract checker counts it as one
   attempted overreach.
8. [~] Add top-level CI or local `make verify`.
   Current state: local `make verify` runs JSON checks, contract validation,
   trace validation, profile validation, compile checks, provenance checks, and
   no-local-path checks. Full done still requires CI wiring.
9. [ ] Create a paper-claim ledger.
   Done when every abstract/introduction/table number has a source manifest or
   result file.

## P1: Claim Contract And Paper Spine

1. [ ] Freeze final research questions.
   Done when one primary RQ is runtime conformance drift and all secondary RQs
   map to measurable artifacts.
2. [ ] Write a threat model section.
   Done when attacker capabilities, benign skill assumptions, adversarial skill
   assumptions, host trust, and non-goals are explicit.
3. [ ] Update related work with May 2026 skill-security papers.
   Done when the paper differentiates against Agent Skills in the Wild,
   SkillScope, Under the Hood of SKILL.md, SkCC, SkillSafetyBench, and relevant
   MCP/tool-security work.
4. [ ] Rewrite the introduction around "runtime as the security variable."
   Done when the first page makes the differential testing contribution clear
   before discussing individual case studies.
5. [ ] Add a reviewer-risk table to the paper notes.
   Done when each likely objection has a planned evidence answer or limitation.
6. [ ] Decide whether the first submission is workshop, short paper, or full
   paper.
   Done when target venue, deadline, page budget, and required evidence level
   are written down.

## P2: Instrumentation Coverage Expansion

1. [ ] Add `activation.*` events to the trace schema.
   Done when discovery, selection, activation, and non-activation can be
   represented and validated.
2. [ ] Add activation instrumentation to at least one plugin-style or
   skill-registry case.
   Done when D1 is measured in an executable case.
3. [ ] Add `approval.*` events to the trace schema.
   Done when requested, decision, bypassed, and not-required actions can be
   represented and correlated to sensitive events.
4. [ ] Implement deterministic approval shim support.
   Done when RP2/RP3/RP6 can deterministically allow or deny approval-required
   operations for benchmark runs.
5. [ ] Add `tool.*` and MCP-style events to the trace schema.
   Done when tool descriptor reads, calls, results, and mutations validate.
6. [ ] Build one controlled MCP/tool workflow fixture.
   Done when `contracts/mcp-tool-workflow-restricted-tools.yaml` has a runnable
   RP profile comparison.
7. [ ] Add persistence events.
   Done when hidden cache writes, retained state, and cleanup leftovers are
   explicit trace events rather than only file diffs.
8. [ ] Add runtime capability snapshot events.
   Done when available privilege can be measured separately from exercised
   privilege.
9. [ ] Update `paper/method-boundaries.md`.
   Done when each newly measured surface has precise coverage and non-coverage
   wording.

## P3: Runtime Profile Expansion

1. [ ] Make RP1 restricted hosted-style executable or explicitly simulated.
   Done when RP1 emits valid traces and a support matrix lists unsupported
   surfaces.
2. [~] Extend RP2 beyond file/network/output evidence.
   Done when RP2 emits approval, activation, tool, and persistence events for
   relevant cases.
3. [~] Extend RP3 beyond current file/network/output evidence.
   Done when RP3 emits blocked write attempts, approval shim events, tool
   events, and persistence events.
4. [ ] Make RP4 MCP-connected executable.
   Done when at least one MCP/tool workflow runs with descriptor and tool-call
   traces.
5. [ ] Make RP5 plugin-style executable.
   Done when at least one install/activation/update surface is measured.
6. [ ] Make RP6 policy-hardened executable.
   Done when the same cases can be run under a hardened mitigation profile.
7. [ ] Create an adapter support matrix.
   Done when every profile lists implemented, simulated, unavailable, and
   intentionally unsupported surfaces.

## P4: Benchmark Expansion

1. [ ] Define case inclusion and exclusion checklist in machine-readable form.
   Done when every case manifest records provenance level, execution level,
   safety boundary, and publication status.
2. [ ] Expand document automation beyond docs-forge.
   Done when at least three document automation skills have benign and
   adversarial variants.
3. [ ] Expand compliance/audit beyond AuditLens.
   Done when at least three compliance or evidence-audit workflows are included.
4. [ ] Add API workflow fixtures.
   Done when mock API tasks cover credential exposure, no-egress policy, and
   approval-required calls.
5. [ ] Add MCP/tool workflow fixtures.
   Done when controlled tool descriptors and restricted resources are covered.
6. [ ] Add persistence/cache fixtures.
   Done when hidden state, resumable state, and cleanup retention are measured.
7. [ ] Add activation-negative-control fixtures.
   Done when skills are tested for non-activation under unrelated tasks.
8. [ ] Add at least 10 skills for a short-paper dataset.
   Done when each has manifest, task prompt, contract, expected outputs, and
   at least two runtime profiles.
9. [ ] Add at least 40 skills for full-paper minimum.
   Done when the benchmark has enough category diversity for aggregate tables.
10. [ ] Separate full product, controlled fixture, and source-only evidence.
    Done when tables never blur these levels.

## P5: Experimental Rigor And Statistics

1. [ ] Add repeat-run command support across all runners.
   Done when repeat IDs can be generated and compared without manual edits.
2. [ ] Run three repeats for deterministic fixtures promoted to paper evidence.
   Done when result tables report repeat stability.
3. [ ] Run five repeats for model-mediated or nondeterministic cases.
   Done when per-repeat and aggregate outcomes are both stored.
4. [ ] Add utility metrics.
   Done when benign task success and missing output are reported beside
   violations.
5. [ ] Add Wilson confidence intervals for simple rates.
   Done when tables include intervals for violation, attempt, and canary rates.
6. [ ] Add bootstrap intervals over skill-task-contract triples.
   Done when category and runtime-pair comparisons have uncertainty estimates.
7. [ ] Add manual adjudication form.
   Done when reviewers can classify findings without editing raw result files.
8. [ ] Run two-reviewer agreement on a sample.
   Done when percent agreement and Cohen's kappa are reported where label
   counts support it.
9. [ ] Add an instrumentation-failure category to metrics.
   Done when missing observer data cannot be mistaken for security success.

## P6: Mitigations And Runtime Report Cards

1. [ ] Define runtime report-card schema.
   Done when each runtime summarizes realized violations, attempted overreach,
   drift disagreements, missing outputs, utility, approval burden, and evidence
   coverage.
2. [ ] Implement RP6 hardened profile policies.
   Done when filesystem, network, approval, tool, and persistence restrictions
   are expressed and validated.
3. [ ] Run RP6 against all MVP case families.
   Done when report cards show whether hardening reduces drift and what utility
   cost it introduces.
4. [ ] Add least-privilege baseline.
   Done when SkillScope-style or contract-derived least privilege rules can be
   compared against runtime-only enforcement.
5. [ ] Add ablation experiments.
   Done when filesystem scope, write scope, network egress, approval policy,
   tool exposure, and persistence can be toggled independently for selected
   cases.
6. [ ] Add mitigation discussion.
   Done when the paper explains deployable runtime controls rather than only
   identifying failures.

## P7: Submission And Artifact Package

1. [ ] Add `SECURITY.md`.
   Done when safe disclosure, synthetic canary policy, and no-real-secret policy
   are explicit.
2. [ ] Add `CITATION.cff`.
   Done when the artifact can be cited cleanly.
3. [ ] Add final license and data card.
   Done when benchmark fixtures and generated results have release terms.
4. [ ] Add artifact anonymity checklist.
   Done when double-blind venues can receive a scrubbed repository without
   author, institution, or local path leakage.
5. [ ] Add AI-use disclosure draft.
   Done when venue-required disclosure language is ready for CCS, S&P, NDSS, or
   USENIX as applicable.
6. [ ] Write paper figures.
   Done when the paper has figures for architecture, trace lifecycle, runtime
   profile matrix, drift outcomes, mitigation report cards, and artifact flow.
7. [ ] Build clean-checkout artifact bundle.
   Done when an external reviewer can reproduce main tables with documented
   commands.
8. [ ] Run final reviewer simulation.
   Done when an internal review produces no critical no-go findings.

## Immediate Next Step

Continue P0 before scaling P4. The next concrete implementation task is:

1. Create the paper-claim ledger so each table and abstract number points to a
   manifest or result file.
2. Emit `workspace_snapshot_hash`, `task_prompt_hash`, and `variant_id` from
   runners so `compare_contract_runs` can enforce the planned invariants.
3. Finish the published pinned-source hash lists for first-party seed repos.
4. Wire `make verify` into CI.

That sequence turns the current verified MVP from a strong local artifact into
a reviewer-ready evidence package.
