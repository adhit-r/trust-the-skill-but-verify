# Refined Research TODO

This TODO is mapped to `REFINED_RESEARCH_ROADMAP.md`. Status values:

- `[ ]` not started
- `[~]` in progress or partially present
- `[x]` complete in the current repo

Only goal: reach top-tier full-paper readiness for NDSS, USENIX Security,
IEEE S&P, or ACM CCS. Workshop, short-paper, demo, and technical-report tracks
are not planning targets. Every TODO below should either increase full-paper
evidence strength or be removed.

## P0: Evidence Integrity Gate

1. [x] Add source-provenance hash verification to
   `experiments/audit-lens-mvp/reproduce_audit_lens_mvp.sh`.
   Done: the script verifies the committed fixture workspace snapshot before
   Docker execution; optional `AUDIT_LENS_SOURCE_ROOT` verification checks the
   pinned commit, pinned tree, and 42 published source blob hashes. The
   provenance verifier now requires the pinned hash list and minimum count.
2. [x] Add source-provenance hash verification to
   `experiments/docs-forge-mvp/reproduce_docs_forge_mvp.sh`.
   Done: the script verifies the committed fixture workspace snapshot before
   Docker execution; optional `DOCS_FORGE_SOURCE_ROOT` verification checks the
   pinned commit, pinned tree, and 11 published source blob hashes. The
   provenance verifier now requires the pinned hash list and minimum count.
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
6. [x] Strengthen `compare_contract_runs` invariants.
   Done: runners emit `workspace_snapshot_hash`, `task_prompt_hash`, and
   `variant_id`; trace start metadata carries those fields; contract findings
   expose them; and `compare_contract_runs` reports no unchecked comparator
   fields across the twelve RP2/RP3 comparison artifacts.
7. [x] Normalize RP3 blocked source mutation as an attempted write event.
   Done: docs-forge P2 RP3 emits a failed `filesystem.write` event for
   `./repo/src/generated-docs.ts`, and the contract checker counts it as one
   attempted overreach.
8. [x] Add top-level CI or local `make verify`.
   Done: local `make verify` runs JSON checks, contract validation, trace
   validation, profile validation, compile checks, provenance checks,
   claim-ledger validation, and no-local-path checks. GitHub Actions now runs
   the same gate on push to `main` and pull requests.
9. [x] Create a paper-claim ledger.
   Done: `paper/claim-ledger.json` maps paper-facing numbers and boundary
   claims to source manifests, result artifacts, or paper notes, and
   `tools/validate_claim_ledger.py` runs from `make verify`.
10. [x] Add clean-clone first-party source verification.
    Done: `experiments/first-party-source-provenance/reproduce_first_party_source_provenance.sh`
    verifies `adhit-r/docs-forge` and `adhit-r/audit-lens` from ephemeral
    clean clones against the pinned commits, trees, and 53 published source
    hashes, producing `results/external/first-party-source-provenance.json`.
11. [x] Add bounded docs-forge live-installer dry-run evidence.
    Done: `experiments/docs-forge-live-installer/reproduce_docs_forge_live_installer.sh`
    runs real Node CLI help/version and two installer dry-run commands against
    a disposable target, verifies zero source/target mutations, and writes
    `results/live/docs-forge-installer/dry_run_result.json`.
12. [x] Add bounded docs-forge project-local non-dry-run installer evidence.
    Done: `experiments/docs-forge-live-project-local-install/reproduce_docs_forge_live_project_local_install.sh`
    runs one real project-local installer command against a disposable target,
    verifies only expected target skill/playbook writes, and writes
    `results/live/docs-forge-installer/project_local_install_result.json`.
13. [x] Add bounded docs-forge live Node runtime-pair scaffold evidence.
    Done: `experiments/docs-forge-live-runtime-pair/reproduce_docs_forge_live_runtime_pair.sh`
    runs the same project-local installer command under host-environment and
    minimal-environment synthetic-home Node profiles, compares output and
    target mutation hashes, and writes
    `results/live/docs-forge-installer/project_local_runtime_pair_result.json`.
14. [x] Add bounded docs-forge live package-observer evidence.
    Done: `experiments/docs-forge-live-package-observer/reproduce_docs_forge_live_package_observer.sh`
    materializes the pinned local npm package with lifecycle scripts disabled,
    verifies the expected tarball entries, and writes
    `results/live/docs-forge-installer/package_observer_result.json`.
15. [x] Add bounded docs-forge live local-tarball npx observer evidence.
    Done: `experiments/docs-forge-live-npx-observer/reproduce_docs_forge_live_npx_observer.sh`
    runs `npx --offline --package <local tarball> docs-forge --help`, verifies
    required help markers, and writes
    `results/live/docs-forge-installer/npx_observer_result.json`.
16. [x] Add bounded docs-forge RP3 Node container local-tarball npx observer evidence.
    Done: `experiments/docs-forge-live-npx-rp3-node-observer/reproduce_docs_forge_live_npx_rp3_node_observer.sh`
    runs the local-tarball npx help workload in a Node-capable RP3-derived
    Docker image with `--network=none` and `--read-only`, and writes
    `results/live/docs-forge-installer/npx_rp3_node_observer_result.json`.
17. [x] Add bounded docs-forge live npx runtime-pair scaffold evidence.
    Done: `experiments/docs-forge-live-npx-runtime-pair/reproduce_docs_forge_live_npx_runtime_pair.sh`
    compares host Node synthetic-home and RP3 Node container local-tarball npx
    observers, verifies zero required pair-check failures, and writes
    `results/live/docs-forge-installer/npx_runtime_pair_result.json`.

## P1: Claim Contract And Paper Spine

1. [x] Freeze final research questions.
   Done: `paper/paper-spine.md` freezes RQ1 as the primary runtime
   conformance-drift question and maps RQ2-RQ6 to measurable artifacts and
   full-paper gates.
2. [x] Write a threat model section.
   Done: `paper/paper-spine.md` records assets, trusted components, runtime
   under test, benign and adversarial skill assumptions, attacker capabilities,
   non-goals, and safe-release boundaries.
3. [x] Update related work with May 2026 skill-security papers.
   Done: `paper/paper-spine.md` and `RELATED_WORK.md` differentiate against
   skill-scanning, malicious-skill, SkillScope, SKILL.md governance, SkCC,
   MCP/tool-security, and prompt-injection benchmark work.
4. [x] Rewrite the introduction around "runtime as the security variable."
   Done: `paper/introduction-skeleton.md` now frames the opening claim around
   fixed skill/task/contract evidence and runtime-conditioned outcomes.
5. [x] Add a reviewer-risk table to the paper notes.
   Done: `paper/paper-spine.md` includes a reviewer-risk table with evidence
   answers or required work for each likely top-tier objection.
6. [x] Select the top-tier full-paper target and deadline plan.
   Done: `paper/paper-spine.md` records NDSS 2027 Fall as the aggressive
   target, IEEE S&P 2027 second cycle as a strong target, USENIX Security 2027
   Cycle 2 as the primary realistic target, and ACM CCS next full cycle as a
   backup top-tier target.

## P2: Instrumentation Coverage Expansion

1. [x] Add `activation.*` events to the trace schema.
   Done: controlled semantic events now represent and validate
   `activation.discover`, `activation.select`, and `activation.not_selected`.
2. [~] Add activation instrumentation to at least one plugin-style or
   skill-registry case.
   Partial: the controlled MCP/tool workflow fixture emits activation events;
   plugin-style discovery and negative-control D1 measurement remain pending.
3. [x] Add `approval.*` events to the trace schema.
   Done: semantic trace ingestion validates `approval.required`,
   `approval.prompt`, and `approval.decision` with request correlation.
4. [~] Implement deterministic approval shim support.
   Partial: the MCP/tool fixture emits deterministic approval records, but
   RP2/RP3/RP6 do not yet enforce a general approval shim.
5. [~] Add `tool.*` and MCP-style events to the trace schema.
   Partial: controlled `tool.call` events validate and contract-check; descriptor
   reads, tool results, and tool mutation events remain pending.
6. [x] Build one controlled MCP/tool workflow fixture.
   Done: `contracts/mcp-tool-workflow-restricted-tools.yaml` now has a runnable
   RP2/RP3 comparison through `tools/run_mcp_tool_workflow_mvp.py`.
7. [~] Add persistence events.
   Partial: controlled `persistence.write` events are explicit in traces; retained
   state and cleanup-leftover semantics remain pending.
8. [x] Add runtime capability snapshot events.
   Done: traces emit `capability.snapshot`, and the smoke traces validate it.
9. [x] Update `paper/method-boundaries.md`.
   Done: the boundary now separates controlled semantic-event coverage from live
   MCP server, connector-auth, commercial approval UX, and complete persistence
   claims.

## P3: Runtime Profile Expansion

1. [ ] Make RP1 restricted hosted-style executable or explicitly simulated.
   Done when RP1 emits valid traces and a support matrix lists unsupported
   surfaces.
2. [~] Extend RP2 beyond file/network/output evidence.
   Partial: RP2 now emits activation, approval, tool-call, and persistence
   semantic events for the controlled MCP/tool workflow case.
3. [~] Extend RP3 beyond current file/network/output evidence.
   Partial: RP3 now emits activation, approval, blocked tool-call, and failed
   persistence semantic events for the controlled MCP/tool workflow case.
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
5. [~] Add MCP/tool workflow fixtures.
   Partial: one controlled restricted-tool workflow fixture now covers approved
   schema/resource tools plus denied discovery/auth/exec tools.
6. [~] Add persistence/cache fixtures.
   Partial: hidden `.skill-cache` writes are measured in the MCP/tool workflow
   fixture; resumable state and cleanup retention remain pending.
7. [ ] Add activation-negative-control fixtures.
   Done when skills are tested for non-activation under unrelated tasks.
8. [ ] Add at least 40 skills for the full-paper benchmark.
   Done when every skill has a manifest, task prompt, contract, expected
   outputs, provenance level, execution level, and publication boundary.
9. [ ] Produce at least 120 skill-task-contract runs before repeats.
   Done when the benchmark supports category-level and runtime-pair-level
   aggregate tables across at least four runtime profiles.
10. [~] Separate full product, controlled fixture, and source-only evidence.
    Partial: tables and method boundaries now include a source-only clean-clone
    provenance level. Full-product execution levels remain pending.

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
3. [ ] Run RP6 against all current benchmark case families.
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

P0 and P1 are now implementation-complete for the current evidence and paper
spine gates. The next concrete implementation sequence is:

1. Add a public-registry observer with explicit network capture, or add
   adversarial npx/package-acquisition variants, before making live docs-forge
   package-acquisition or runtime-drift claims.
2. Close P2/P3 coverage gaps for activation, approval, tool/MCP, persistence,
   and at least four runtime profiles.
3. Scale P4 to 40+ skills and 120+ skill-task-contract runs before repeats.
4. Complete P5/P6 rigor: repeats, uncertainty, utility, adjudication,
   reviewer agreement, and mitigation/report-card baselines.
5. Complete P7 artifact and manuscript packaging for anonymous top-tier review.

There is no short-paper fallback in this roadmap.
