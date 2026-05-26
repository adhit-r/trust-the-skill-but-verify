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
| CL-MVP-003 | Fifty tracked trace files including older smoke traces, bounded RP4 fixture traces, and RP6 current-case report-card traces | `results/raw/*/trace.jsonl` |
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
| CL-REP-002 | Planned-inclusion RP2/RP3 deterministic repeat-stability check covers 44 controlled fixtures across repeat IDs 1, 2, and 3, with 264 trace-valid observations and 132 same-repeat pairs; statistical, prevalence, reviewer-agreement, and defense-success claims remain unsupported | `results/fixtures/strengthening/rp2-rp3-repeat-stability/repeat_stability.json` |
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
| CL-P1-001 | Paper spine freezes the top-tier thesis, RQs, threat model, reviewer risks, and venue backplan | `paper/paper-spine.md` |
| CL-CASE-001 | Repo-audit adversarial RP2/RP3 outcome counts | Baseline manifest and repo-audit result artifacts |
| CL-CASE-002 | Network-egress adversarial RP2/RP3 outcome counts | Baseline manifest and network-egress result artifacts |
| CL-CASE-003 | AuditLens contributes one drift claim and seven pairwise disagreements | Baseline manifest |
| CL-CASE-004 | docs-forge contributes two drift claims and eight pairwise disagreements | Baseline manifest |
| CL-CASE-005 | MCP/tool workflow adversarial RP2/RP3 outcome counts | Baseline manifest and MCP/tool workflow result artifacts |
| CL-GATE3-001 | Current benchmark manifest records 20 skills and 60 skill-task-contract triples after promoting planned synthetic entries to controlled single-repeat RP2/RP3 fixture evidence, without claiming source-mix completion, repeat stability, prevalence, live product behavior, or the 40/120 full-paper floor | `benchmark/manifests/benchmark-cases-current.json` |
| CL-GATE3-002 | Derived runtime report-card package contains deterministic report cards for RP1, RP2, RP3, RP5, and RP6 | `results/derived/runtime-report-cards/` |
| CL-GATE3-003 | Benchmark scale-gap report shows zero numeric shortfall against the 20/60 inventory target, a remaining 20-skill / 60-triple shortfall against the 40/120 full-paper floor, and skill-origin source-mix gaps of 4 first-party / 7 public skills for mid-scale and 8 first-party / 16 public skills for full-paper, without claiming source-mix completion | `results/derived/benchmark-scale-gap.json` |
| CL-GATE3-004 | Controlled executable extension adds 2 synthetic fixture families, 6 RP2/RP3 comparison artifacts, and 12 referenced traces for data extraction and local file operations, with zero runtime-drift claims and zero pairwise disagreements | `results/mvp/data-extraction/`, `results/mvp/local-file-operation/` |
| CL-GATE3-006 | Formerly planned inclusion batch contributes 44 controlled single-repeat RP2/RP3 synthetic fixture comparisons, 88 contract-finding files, and 88 unique traces, with zero runtime-drift claims and zero pairwise disagreements | `results/planned-inclusion/` |
| CL-GATE5-001 | Paired-runtime summary aggregates 90 existing comparison artifacts into 142 pair records as a denominator layer, while explicitly excluding completed statistics and reviewer agreement | `results/derived/paired-runtime-summary.json` |
| CL-GATE5-002 | Gate 5 frozen inclusion table includes 60 current benchmark cases, and the descriptive-rate artifact reports 22 raw inventory and coverage rate records without claiming completed statistics, intervals, hypothesis tests, reviewer agreement, prevalence, source-mix completion, or paper-grade completion | `results/derived/gate5-descriptive-rates.json` |
| CL-GATE5-003 | Gate 5 manual review queue enumerates 60 queued case-level review items, including 50 paired-summary mapped and first-pass blinding-eligible items plus 10 metadata-only unmapped items, without claiming completed reviews, reviewer agreement, adjudication, statistics, prevalence, or paper-grade completion | `benchmark/review/gate5-review-queue.json` |
| CL-GATE5-004 | Gate 5 review-packet index expands the queue into 60 packet-index records with 50 comparison refs, 100 run/finding-file refs, 100 trace refs, 50 runtime-pair review units, and 10 metadata-only blocked packets, without claiming raw trace content, completed reviews, reviewer agreement, adjudication, statistics, prevalence, or paper-grade completion | `benchmark/review/gate5-review-packet-index.json` |
| CL-GATE5-005 | Gate 5 blinded packet bundle derives from the frozen packet index and exports 50 first-pass runtime-label-blinded pair-review packets while keeping 10 unmapped packets blocked as metadata-only records, without claiming raw trace content, completed reviews, reviewer agreement, adjudication, statistics, prevalence, commercial-runtime behavior, or paper-grade completion | `benchmark/review/gate5-blinded-packet-bundle.json` |
| CL-GATE5-006 | Gate 5 review export template package creates two blank first-pass human-review templates over the same 50 blinded pair-review units while keeping 10 unmapped packets blocked, without claiming completed human reviews, human reviewer identities, Codex-assisted human-review substitution, reviewer agreement, adjudication, statistics, prevalence, or paper-grade completion | `benchmark/review/gate5-review-export-templates.json` |

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
