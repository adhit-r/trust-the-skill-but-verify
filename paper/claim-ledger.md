# Paper Claim Ledger

This ledger maps paper-facing claims to current repository evidence. The
machine-readable source of truth is `paper/claim-ledger.json`; validate it with:

```bash
python3 tools/validate_claim_ledger.py
```

## Claim Boundary

The current baseline evidence supports feasibility and method claims only. It does not support
ecosystem prevalence claims, commercial-runtime claims, full product execution
claims, public-internet testing claims, or syscall-complete tracing claims.

## Supported Numerical Claims

| Claim ID | Claim | Evidence |
| --- | --- | --- |
| CL-MVP-001 | Five controlled case families | `benchmark/manifests/skilldiff-mvp-baseline.json` |
| CL-MVP-002 | Twenty-eight paper-facing canonical trace files | `benchmark/manifests/skilldiff-mvp-baseline.json` |
| CL-MVP-003 | 234 tracked raw trace files including older smoke traces, expanded runtime fixtures, bounded RP4 fixture traces, and RP6 current-case report-card traces | `results/raw/*/trace.jsonl` |
| CL-MVP-004 | Five runtime-drift claims across RP2/RP3 | `benchmark/manifests/skilldiff-mvp-baseline.json` |
| CL-MVP-005 | Thirty-six pairwise disagreements across RP2/RP3 | `benchmark/manifests/skilldiff-mvp-baseline.json` |
| CL-MVP-007 | Two first-party seed case families: AuditLens and docs-forge | Baseline manifest |
| CL-MVP-008 | Three controlled synthetic case families: repo-audit, network-egress, and MCP/tool workflow | Baseline manifest |
| CL-MVP-009 | Fourteen RP2/RP3 comparison JSON files and twenty-eight contract-finding JSON files | `results/mvp/*/*.json` |
| CL-MVP-010 | RP2/RP3 comparison artifacts have no unchecked comparator fields | `results/mvp/*/*_rp2_rp3_comparison.json` |
| CL-MVP-011 | First-party manifests publish verifier-required pinned source hash lists: 11 docs-forge entries and 42 AuditLens entries | First-party source manifests |
| CL-RP6-001 | RP6 current-case report card covers fourteen existing case variants with zero realized violations, twelve blocked attempted-overreach findings, seven missing outputs, zero canary observations, and one supplemental network-denial policy probe | `results/fixtures/rp6-policy-hardened/report_card.json` |
| CL-RP1-001 | RP1 deterministic restricted-hosted simulator covers twelve upload-oriented current-subset variants with zero realized violations, two blocked attempted-overreach findings, sixteen missing outputs, and zero canary observations; this is simulator-backed evidence only | `results/fixtures/rp1-restricted-hosted/report_card.json` |
| CL-RP5-001 | RP5 plugin-style fixture covers three local plugin lifecycle cases with one activation negative control, zero realized violations, one blocked attempted-overreach finding, zero missing outputs, and zero canary observations; this is fixture-backed evidence only | `results/fixtures/rp5-plugin-style/report_card.json` |
| CL-SCAN-001 | Static scanner baseline covers fourteen variants and forty-eight controlled fixture source files, producing eighty-eight source-only static findings with no runtime, prevalence, or defense-success claim | `results/fixtures/strengthening/static_scanner_baseline.json` |
| CL-REACH-001 | Semia-style reachability approximation covers fourteen variants and eighty-eight bounded candidates, with zero Semia equivalence, Semia reproduction, or runtime-confirmation claims supported | `results/fixtures/strengthening/reachability_approximation.json` |
| CL-ACT-001 | Action-boundary baseline checks fourteen controlled fixture commands, all contract-allowed and fixture-scoped, with zero review flags and zero ClawGuard/Task Shield reproduction claims supported | `results/fixtures/strengthening/action_boundary_baseline.json` |
| CL-LP-001 | Contract-derived least-privilege baseline covers fourteen variants and seven contracts with all benign and adversarial expectations passing against RP6 report-card outcomes | `results/fixtures/strengthening/least_privilege_baseline.json` |
| CL-MIT-001 | Coarse RP2/RP3/RP6 mitigation ladder observes lower RP6 realized-violation and canary-observation counts than RP2 while surfacing RP6 missing-output cost; minimal contrast matrix covers eight selected variants plus one network policy probe | `results/fixtures/strengthening/rp6_mitigation_ladder.json` |
| CL-ABL-001 | Bounded RP6 component-ablation report card covers six controls across twelve generated RP6 ablation traces, with benign and adversarial/probe coverage for every component and thirteen realized-violation delta plus two canary-observation delta under disabled controls | `results/fixtures/rp6-policy-hardened/ablations/component_report_card.json` |
| CL-REP-001 | Bounded RP6 deterministic repeat-stability check covers fourteen variants across repeat IDs 1, 2, and 3, with 42 trace-valid observations and matching outcome summaries; statistical repeat-stability claims remain unsupported | `results/fixtures/strengthening/repeat-stability/repeat_stability.json` |
| CL-REP-002 | Planned-inclusion RP2/RP3 deterministic repeat-stability check covers 116 controlled fixtures across repeat IDs 1, 2, and 3, with 696 trace-valid observations and 348 same-repeat pairs; statistical, prevalence, reviewer-agreement, and defense-success claims remain unsupported | `results/fixtures/strengthening/rp2-rp3-repeat-stability/repeat_stability.json` |
| CL-REP-003 | Current main RP2/RP3 deterministic repeat-stability check covers 13 controlled fixtures across repeat IDs 1, 2, and 3, with 78 trace-valid observations and 39 same-repeat pairs; statistical, prevalence, reviewer-agreement, live-product, public-network, commercial-runtime, and defense-success claims remain unsupported | `results/fixtures/strengthening/rp2-rp3-main-repeat-stability/repeat_stability.json` |
| CL-REP-004 | Source-mix RP6 deterministic repeat-stability check covers 74 first-party/public controlled fixtures across repeat IDs 1, 2, and 3, with 222 trace-valid RP6 observations and matching outcome summaries excluding event count; source-mix-completion, statistical, model-mediated, runtime-drift, prevalence, human-review, commercial-runtime, public-network, and defense-success claims remain unsupported | `results/fixtures/strengthening/source-mix-rp6-repeat-stability/repeat_stability.json` |
| CL-REP-005 | Repeat-coverage validation cross-checks the four repeat-backed buckets while keeping RP1/RP5 report-card-only, metadata-only, model-mediated, McNemar, human-review, reviewer-agreement, prevalence, source-mix-completion, commercial-runtime, and defense-success boundaries explicit | `tools/validate_repeat_coverage.py` |
| CL-EXT-001 | First-party docs-forge and AuditLens source repositories verify from clean ephemeral clones against pinned commits, trees, and 53 source hashes | `results/external/first-party-source-provenance.json` |
| CL-EXT-003 | Bounded docs-forge Node CLI help/version and two installer dry-run commands pass without target/source mutations | `results/live/docs-forge-installer/dry_run_result.json` |
| CL-EXT-004 | Bounded docs-forge project-local non-dry-run install passes with only expected project-local install files and no source, home, or unexpected target mutations | `results/live/docs-forge-installer/project_local_install_result.json` |
| CL-EXT-005 | Bounded docs-forge live Node runtime-pair scaffold compares host-environment and minimal-environment synthetic-home installs with zero target-output disagreements and zero runtime-drift claims | `results/live/docs-forge-installer/project_local_runtime_pair_result.json` |
| CL-EXT-006 | Bounded docs-forge live package-observer materializes one expected local npm tarball with ten expected entries and no npx execution, install command, lifecycle scripts, source mutation, or runtime-drift claim | `results/live/docs-forge-installer/package_observer_result.json` |
| CL-EXT-007 | Bounded docs-forge live local-tarball npx observer executes docs-forge help through npx offline with no registry acquisition, package-name npx command, install command, lifecycle scripts, source mutation, or runtime-drift claim | `results/live/docs-forge-installer/npx_observer_result.json` |
| CL-EXT-008 | Bounded docs-forge live RP3 Node container observer executes docs-forge help through npx offline under Docker network denial and read-only root filesystem constraints with no registry acquisition, package-name npx command, install command, lifecycle scripts, source mutation, or runtime-drift claim | `results/live/docs-forge-installer/npx_rp3_node_observer_result.json` |
| CL-EXT-009 | Bounded docs-forge live local-tarball npx runtime-pair scaffold compares host Node synthetic-home and RP3 Node container observers with zero required pair-check failures and zero runtime-drift claims | `results/live/docs-forge-installer/npx_runtime_pair_result.json` |
| CL-EXT-010 | Bounded docs-forge adversarial package-name npx observer fails closed against a loopback registry with no public registry acquisition, install command, lifecycle scripts, source/home mutation, or runtime-drift claim | `results/live/docs-forge-installer/npx_adversarial_package_acquisition_result.json` |
| CL-EXT-011 | Bounded docs-forge RP3 Node adversarial package-name npx observer fails closed against a controlled nonpublic registry target inside a Node-capable RP3-derived container, with no public registry acquisition, install command, lifecycle scripts, source/home mutation, packet-capture claim, or runtime-drift claim | `results/live/docs-forge-installer/npx_rp3_node_adversarial_package_acquisition_result.json` |
| CL-EXT-012 | Bounded docs-forge adversarial host-vs-RP3 runtime-pair scaffold compares host Node synthetic-home and RP3 Node container package-name npx fail-closed observers with zero required pair-check failures and zero runtime-drift claims | `results/live/docs-forge-installer/npx_adversarial_package_acquisition_runtime_pair_result.json` |
| CL-EXT-013 | Bounded ripgrep public live local-binary fixture executes two local `rg` commands over a copied synthetic allowlisted workspace with one negative-control zero-match command, zero workspace mutations, and no runtime-drift claim | `results/live/ripgrep-public-local-binary/live_local_binary_search_result.json` |
| CL-EXT-014 | Safe real-run promotion decision gate classifies existing bounded local live slices and blocks credentialed, public-network, commercial-runtime, and full-product candidates without adding new live execution or runtime-drift claims | `docs/research/safe-real-run-promotion-decisions.json` |
| CL-P1-001 | Paper spine freezes the top-tier thesis, RQs, threat model, reviewer risks, and venue backplan | `paper/paper-spine.md` |
| CL-P1-002 | Paper-facing evidence-boundary matrix separates current executable evidence, promoted bounded evidence, review-ready scaffolds, and future work while preserving runtime-report-card and human-review nonclaim boundaries | `paper/tables/evidence-boundary-matrix.md` |
| CL-P1-003 | Introduction draft and README state the full fixed-invariant/runtime-variable framing while preserving no-prevalence, no-commercial-runtime, no-public-internet-exfiltration, no-defense-success, and no-completed-human-review boundaries | `paper/introduction-skeleton.md`; `README.md` |
| CL-P1-004 | Paper figure package contains six canonical SVG figures with manifest and verifier-backed boundaries for no-new-experimental-results, no-prevalence, no-commercial-runtime, no-public-network-exfiltration, no-syscall-complete-tracing, no-defense-success, and no-completed-human-review claims | `paper/figures/manifest.json`; `paper/figures.md` |
| CL-P1-005 | Related-work refresh uses current primary sources for the crowded skill-security and MCP-security map while preserving positioning-only boundaries | `docs/research/related-work.md`; `paper/paper-spine.md` |
| CL-P1-006 | Artifact-release path provides one-command machine-only paper-table reproduction plus curated local bundle builder/validator, without whole-repo archive, public-release, external-review, completed-human-review, secret/auth/cookie, raw-scratch, or public-network claims | `scripts/reproduce_paper_tables.sh`; `tools/build_artifact_release_bundle.py`; `tools/validate_artifact_release_bundle.py` |
| CL-P1-007 | Methodology and limitation prose includes reviewer-objection responses plus machine-checked claim-boundary validation without firstness, prevalence, defense-success, Semia-equivalence, commercial-runtime, public-release, external-review, or completed-human-review claims | `paper/method-boundaries.md`; `tools/validate_paper_claim_boundaries.py` |
| CL-CASE-001 | Repo-audit adversarial RP2/RP3 outcome counts | Baseline manifest and repo-audit result artifacts |
| CL-CASE-002 | Network-egress adversarial RP2/RP3 outcome counts | Baseline manifest and network-egress result artifacts |
| CL-CASE-003 | AuditLens contributes one drift claim and seven pairwise disagreements | Baseline manifest |
| CL-CASE-004 | docs-forge contributes two drift claims and eight pairwise disagreements | Baseline manifest |
| CL-CASE-005 | MCP/tool workflow adversarial RP2/RP3 outcome counts | Baseline manifest and MCP/tool workflow result artifacts |
| CL-GATE3-001 | Current benchmark manifest records 44 skills and 132 skill-task-contract triples after adding 24 first-party/public source-provenance families; seventy-two selected source-mix cases across twenty-four first-party/public families have controlled RP2/RP3 fixture evidence and the current source-mix metadata-only count is zero, without claiming source-mix evidence completion, prevalence, live product behavior, or paper-grade 40/120 execution completion | `benchmark/manifests/benchmark-cases-current.json` |
| CL-GATE3-002 | Derived runtime report-card package contains deterministic report cards for RP1, RP2, RP3, RP5, and RP6 | `results/derived/runtime-report-cards/` |
| CL-GATE3-003 | Benchmark scale-gap report shows zero numeric and source-mix shortfall against both the 20/60 mid-scale target and the 40/120 full-paper manifest floor, while not claiming source-mix evidence completion, repeat/statistical readiness, prevalence, or paper-grade full-paper completion | `results/derived/benchmark-scale-gap.json` |
| CL-GATE3-004 | Controlled executable extension adds 2 synthetic fixture families, 6 RP2/RP3 comparison artifacts, and 12 referenced traces for data extraction and local file operations, with zero runtime-drift claims and zero pairwise disagreements | `results/mvp/data-extraction/`, `results/mvp/local-file-operation/` |
| CL-GATE3-006 | Formerly planned inclusion batch contributes 116 controlled single-repeat RP2/RP3 fixture comparisons, 232 contract-finding files, and 232 unique traces, with zero runtime-drift claims and zero pairwise disagreements | `results/planned-inclusion/` |
| CL-GATE3-007 | Source-mix RP6 report card covers 74 first-party/public controlled fixtures across 26 families, with 25 first-party cases, 49 public cases, 74 completed RP6 runs, zero realized violations, zero attempted overreach, zero missing outputs, zero oracle failures, and zero canary observations; this is bounded mitigation/report-card evidence only | `results/fixtures/strengthening/source-mix-rp6-report-card/report_card.json` |
| CL-GATE5-001 | Paired-runtime summary aggregates 162 existing comparison artifacts into 214 pair records as a denominator layer, while explicitly excluding completed statistics, reviewer agreement, and source-mix RP6 report-card statistics | `results/derived/paired-runtime-summary.json` |
| CL-GATE5-002 | Gate 5 frozen inclusion table includes 132 current benchmark cases, and the descriptive-rate artifact reports 22 raw inventory and coverage rate records without claiming completed statistics, intervals, hypothesis tests, reviewer agreement, prevalence, source-mix evidence completion, or paper-grade completion | `results/derived/gate5-descriptive-rates.json` |
| CL-GATE5-003 | Gate 5 manual review queue enumerates 132 queued case-level review items, including 122 paired-summary mapped and first-pass blinding-eligible items plus 10 metadata-only unmapped items, without claiming completed reviews, reviewer agreement, adjudication, statistics, prevalence, or paper-grade completion | `benchmark/review/gate5-review-queue.json` |
| CL-GATE5-004 | Gate 5 review-packet index expands the queue into 132 packet-index records with 122 comparison refs, 244 run refs, 244 trace refs, zero finding refs, 122 runtime-pair review units, and 10 metadata-only blocked packets, without claiming raw trace content, completed reviews, reviewer agreement, adjudication, statistics, prevalence, or paper-grade completion | `benchmark/review/gate5-review-packet-index.json` |
| CL-GATE5-005 | Gate 5 blinded packet bundle derives from the frozen packet index and exports 122 first-pass runtime-label-blinded pair-review packets while keeping 10 unmapped packets blocked as metadata-only records, without claiming raw trace content, completed reviews, reviewer agreement, adjudication, statistics, prevalence, commercial-runtime behavior, or paper-grade completion | `benchmark/review/gate5-blinded-packet-bundle.json` |
| CL-GATE5-006 | Gate 5 review export template package creates two blank first-pass human-review templates over the same 122 blinded pair-review units while keeping 10 unmapped packets blocked, without claiming completed human reviews, human reviewer identities, Codex-assisted human-review substitution, reviewer agreement, adjudication, statistics, prevalence, or paper-grade completion | `benchmark/review/gate5-review-export-templates.json` |
| CL-GATE5-007 | Gate 5 non-human interval artifact computes 36 Wilson intervals, 18 case-bootstrap intervals, 6 hierarchical skill/case bootstrap intervals, and paired-runtime majority/median/max-severity summaries over the curated 132-case denominator and 214 paired-runtime pair records, while keeping completed human review at zero and making no McNemar, reviewer-agreement, adjudication, prevalence, source-mix evidence-completion, commercial-runtime-behavior, defense-success, or paper-grade-completion claim | `results/derived/gate5-statistical-intervals.json` |
| CL-STEER-001 | Current benchmark manifest contains 132 cases and the former four null oracle-ref smoke/report-card cases now point to bounded expected-output oracle metadata; this closes a steering blocker only, not paper-grade evidence completion | `benchmark/manifests/benchmark-cases-current.json`; `benchmark/expected/network-egress/fake-sink-egress-smoke.json`; `benchmark/expected/rp5-plugin-style/*.json`; `tools/validate_benchmark_cases.py` |

## Boundary Claims

| Claim ID | Boundary |
| --- | --- |
| CL-MVP-006 | Current executable baseline runtime-drift comparisons are limited to RP2 and RP3; RP1 simulator and RP6 report-card artifacts are excluded from those aggregate counts. |
| CL-BOUNDARY-001 | Current baseline evidence is not ecosystem prevalence evidence. |
| CL-BOUNDARY-002 | Current baseline does not claim full docs-forge product/docs-generation execution, successful/public-registry npx package-acquisition behavior, or full AuditLens product/live connector execution. |
| CL-BOUNDARY-003 | Current baseline does not claim public-internet testing, packet capture, DNS tracing, or syscall-complete host tracing. |
| CL-BOUNDARY-004 | Publishable artifacts use synthetic canaries only, do not retain raw payloads, and keep public internet contact outside the benchmark boundary. |
| CL-BOUNDARY-005 | Static scanner, reachability approximation, and action-boundary baseline artifacts are bounded comparator/mitigation evidence only; they are excluded from MVP runtime-drift counts and do not imply Semia equivalence, live guardrail efficacy, ClawGuard reproduction, or Task Shield reproduction. |
| CL-EXT-002 | External-validity scaffold entries are source-only and excluded from MVP runtime-drift counts until live traces and comparisons exist. |
| CL-RQ-001 | Current baseline evidence supports RQ1/RQ4 for RP2/RP3, adds RP1 simulator and RP5 plugin-style fixture evidence outside drift aggregates, partially supports RQ2 and RQ3/RQ5 only for controlled semantic-event representation, and has bounded static scanner, reachability approximation, action-boundary, least-privilege, mitigation-ladder, RP6 report-card, and RP6 ablation evidence for RQ6 without Semia equivalence, live guardrail efficacy, or defense-success claims. |

## Design Targets

| Claim ID | Target |
| --- | --- |
| CL-TARGET-001 | Full-paper evidence floor is at least 40 skills and 120 skill-task-contract triples before repeats. |
| CL-TARGET-002 | Full-paper repeat plan is three repeats for deterministic controlled fixtures and five repeats for nondeterministic runs. |

## Maintenance Rule

Any paper text that adds or changes a number must add or update a claim-ledger
entry in `paper/claim-ledger.json`. The validator must run in `make verify`.
