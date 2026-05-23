# Low-Level Research Todo

This file maps implementation and writing tasks to the high-level roadmap in `RESEARCH_ROADMAP.md`.

Status key:

- `[ ]` Not started
- `[~]` In progress
- `[x]` Done
- `[?]` Blocked or needs decision

## Immediate Priority

1. [x] [RM-01] Freeze the working title as `Trust the Skill, Verify the Runtime: Differential Security Testing for Portable AI Agent Skills`.
2. [ ] [RM-01] Rewrite the old DOCX framing so the main contribution is differential runtime testing, not a policy compiler.
3. [x] [RM-04] Define the five drift classes in one page with examples.
4. [~] [RM-07] Build the smallest trace harness; MVP captures process launches, Python-level file reads for controlled Python commands, RP3 container-strace MVP file reads for supported container `open`, `openat`, and `openat2` syscalls, writes, outputs, canaries, PV-02 controlled Python fake-sink plus blocked RP3 egress evidence, and controlled semantic activation/approval/tool/persistence events for the MCP/tool workflow fixture. Broader syscall/network/live-MCP/approval/persistence completeness remains pending.
5. [x] [RM-08] Create the MVP repo-audit benign skill and adversarial variant.
6. [x] [RM-09] Produce the first RP2/RP3 contract-evidence report with an adversarial runtime-drift candidate and MVP Python-level read provenance.
7. [x] [RM-08] Onboard `adhit-r/docs-forge` as the first realistic documentation-skill case study with a controlled Python fixture, pinned provenance, and RP2/RP3 traces.
8. [x] [RM-08] Onboard `adhit-r/audit-lens` as the first realistic compliance-skill case study with a sanitized runnable Acme fixture and RP2/RP3 traces.
9. [x] [RM-08] Add bounded docs-forge live Node CLI dry-run evidence without changing MVP runtime-drift counts.
10. [x] [RM-08] Add bounded docs-forge project-local non-dry-run installer evidence without changing MVP runtime-drift counts.
11. [x] [RM-08] Add bounded docs-forge live Node runtime-pair scaffold evidence without changing MVP runtime-drift counts.
12. [x] [RM-08] Add bounded docs-forge live package-observer evidence without changing MVP runtime-drift counts.

## RM-01: Research Claim and Scope

Goal: make the paper's novelty obvious and defensible.

Tasks:

- [x] [RM-01] Write a one-paragraph problem statement.
- [x] [RM-01] Write a one-sentence thesis.
- [x] [RM-01] Write a "what this paper is" list.
- [x] [RM-01] Write a "what this paper is not" list.
- [x] [RM-01] Define the terms `skill`, `runtime`, `runtime profile`, `skill-task pair`, `security contract`, `trace`, `drift`, and `canary`.
- [x] [RM-01] Create a short motivating example involving a repo-audit skill.
- [x] [RM-01] Show the same skill under three runtime policies: restricted hosted, local coding agent, Docker sandbox.
- [x] [RM-01] Specify the exact bad outcome in the motivating example: `.env` canary read, unauthorized network attempt, or silent write.
- [x] [RM-01] Decide whether the paper uses "semantic drift", "security drift", or "runtime-induced drift" as the main phrase.
- [x] [RM-01] Add a short reviewer-facing novelty statement: "We test whether portability preserves security behavior."

Acceptance checks:

- [x] [RM-01] A reviewer can understand the contribution without reading the system section.
- [x] [RM-01] The claim does not sound like another registry scanner.
- [x] [RM-01] The claim does not sound like another least-privilege compiler.

## RM-02: Related Work and Differentiation

Goal: prevent the work from being rejected as incremental.

Tasks:

- [x] [RM-02] Create a related-work spreadsheet or Markdown table.
- [x] [RM-02] Add Agent Skills in the Wild.
- [x] [RM-02] Add Malicious Agent Skills in the Wild.
- [x] [RM-02] Add SkillScope.
- [x] [RM-02] Add Under the Hood of SKILL.md.
- [x] [RM-02] Add SkCC.
- [x] [RM-02] Add Agent Skills for Large Language Models.
- [x] [RM-02] Add MCP tool poisoning and threat-model papers.
- [x] [RM-02] Add non-agent supply-chain security analogies: browser extensions, npm packages, VS Code extensions, CI/CD actions.
- [x] [RM-02] For each paper, record dataset, method, threat model, artifact, and gap.
- [x] [RM-02] Write a paragraph explaining why static scanning cannot detect runtime-induced drift.
- [x] [RM-02] Write a paragraph explaining why least privilege is a mitigation, not the measurement problem.
- [x] [RM-02] Write a paragraph explaining why cross-framework compilation is not the same as security conformance.
- [x] [RM-02] Identify terms already used by other papers to avoid confusing naming.

Acceptance checks:

- [x] [RM-02] The related-work section names the closest competitor directly.
- [x] [RM-02] The differentiation is specific enough to survive reviewer comparison.
- [x] [RM-02] Claims about related papers are backed by citations.

## RM-03: Threat Model and Security Goals

Goal: define what attacks count and what attacks are out of scope.

Tasks:

- [ ] [RM-03] Define attacker control over SKILL.md instructions.
- [ ] [RM-03] Define attacker control over metadata and broad trigger descriptions.
- [ ] [RM-03] Define attacker control over bundled scripts.
- [ ] [RM-03] Define attacker control over templates, examples, and resources.
- [ ] [RM-03] Define attacker control over declared dependencies.
- [ ] [RM-03] Define attacker goals: secret read, secret propagation, unauthorized sink, hidden persistence, silent tool call, approval bypass.
- [ ] [RM-03] Define defender goals: task success, least necessary privilege, comparable approvals, no unauthorized sinks.
- [ ] [RM-03] Declare out of scope: OS sandbox escape, cryptographic compromise, real credential theft, live victim systems.
- [ ] [RM-03] Write a synthetic-secret policy.
- [ ] [RM-03] Write a local fake network sink policy.
- [x] [RM-03/PV-02] State that benchmark network tests must not contact the public internet.
- [x] [RM-03/PV-02] State that network payloads, query strings, and sensitive headers are redacted or hashed by default.
- [ ] [RM-03] Write a safe artifact release policy.
- [ ] [RM-03] Decide how much adversarial skill content can be published.
- [ ] [RM-03] Add an ethics section placeholder to the paper outline.

Acceptance checks:

- [ ] [RM-03] Every experiment maps to an attacker capability.
- [ ] [RM-03] Every sensitive behavior has a safe synthetic substitute.
- [ ] [RM-03] The artifact can be published without real exfiltration payloads.

## RM-04: Drift Taxonomy and Metrics

Goal: make drift measurable.

Tasks:

- [x] [RM-04] Define D1 activation drift.
- [x] [RM-04] Define D2 privilege drift.
- [x] [RM-04] Define D3 approval drift.
- [x] [RM-04] Define D4 side-effect drift.
- [x] [RM-04] Define D5 data-flow drift.
- [x] [RM-04] Decide whether persistence drift is part of side-effect drift or its own metric.
- [x] [RM-04] Define contract violation rate.
- [x] [RM-04] Define attempted overreach rate separately from realized contract violation rate.
- [x] [RM-04] Define runtime-pair drift rate.
- [x] [RM-04] Define skill-level drift score.
- [x] [RM-04] Define runtime-level risk score.
- [x] [RM-04] Define attack success rate.
- [x] [RM-04] Define benign task success.
- [x] [RM-04] Define approval burden.
- [x] [RM-04] Define false positive and false negative cases.
- [x] [RM-04] Create formulas for each metric.
- [x] [RM-04] Create one example trace for each drift class.
- [x] [RM-04] Decide severity levels: low, medium, high, critical.
- [x] [RM-04] Map each severity level to evidence.

Acceptance checks:

- [x] [RM-04] Metrics can be computed automatically from traces.
- [x] [RM-04] Each metric has a clear numerator and denominator.
- [x] [RM-04] The taxonomy handles both malicious and benign accidental overreach.
- [x] [RM-04] Blocked unsafe attempts are separated from realized security failures.

## RM-05: Security Contract Model

Goal: define expected behavior before running experiments.

Tasks:

- [x] [RM-05] Create `schemas/security_contract.schema.json`.
- [x] [RM-05] Create a YAML example for repo-audit skill.
- [x] [RM-05] Add fields for allowed filesystem reads.
- [x] [RM-05] Add fields for denied filesystem reads.
- [x] [RM-05] Add fields for allowed filesystem writes.
- [x] [RM-05] Add fields for denied filesystem writes.
- [x] [RM-05] Add fields for allowed shell commands.
- [x] [RM-05] Add fields for denied shell commands.
- [x] [RM-05] Add fields for allowed network domains.
- [x] [RM-05] Add fields for denied network domains.
- [x] [RM-05] Add fields for allowed tool calls.
- [x] [RM-05] Add fields for denied tool calls.
- [x] [RM-05] Add fields for approval-required events.
- [x] [RM-05] Add fields for allowed sinks.
- [x] [RM-05] Add fields for denied sinks.
- [x] [RM-05] Add fields for canary labels.
- [x] [RM-05] Add fields for expected functional outputs.
- [x] [RM-05] Add fields for severity overrides.
- [x] [RM-05] Implement contract validation.
- [x] [RM-05] Implement path matching with glob support.
- [x] [RM-05] Implement domain matching.
- [x] [RM-05] Implement command matching.
- [x] [RM-05] Document contract authoring rules.
- [x] [RM-05] Write 10 initial contracts.

Acceptance checks:

- [x] [RM-05] Invalid contracts fail validation with useful errors.
- [x] [RM-05] Contracts can express both expected and forbidden behavior.
- [x] [RM-05] Contracts are task-specific, not only skill-wide.

## RM-06: Runtime Profiles and Adapters

Goal: make runtime differences explicit and reproducible.

Tasks:

- [x] [RM-06] Create `runtimes/profiles/RP1_restricted_hosted.yaml`.
- [x] [RM-06] Create `runtimes/profiles/RP2_local_coding_agent.yaml`.
- [x] [RM-06] Create `runtimes/profiles/RP3_docker_sandbox.yaml`.
- [x] [RM-06] Create `runtimes/profiles/RP4_mcp_connected.yaml`.
- [x] [RM-06] Create `runtimes/profiles/RP5_plugin_style.yaml`.
- [x] [RM-06] Create `runtimes/profiles/RP6_policy_hardened.yaml`.
- [x] [RM-06] Define filesystem access fields for each profile.
- [x] [RM-06] Define shell access fields for each profile.
- [x] [RM-06] Define network access fields for each profile.
- [x] [RM-06] Define credential exposure fields for each profile.
- [x] [RM-06] Define context inheritance fields for each profile.
- [x] [RM-06] Define persistence fields for each profile.
- [x] [RM-06] Define approval semantics for each profile.
- [x] [RM-06] Define tool availability for each profile.
- [x] [RM-06] Implement adapter interface: `prepare`, `run`, `collect`, `cleanup`.
- [x] [RM-06] Implement MVP local adapter dry-run scaffold.
- [x] [RM-06] Implement MVP Docker adapter dry-run scaffold.
- [x] [RM-06] Add a profile feature matrix to documentation.
- [x] [RM-06] Create `schemas/runtime_profile.schema.json`.
- [x] [RM-06] Implement runtime profile validation and canonical hash checks.
- [x] [RM-06] Add a dry-run adapter smoke test for RP2 and RP3.

Acceptance checks:

- [x] [RM-06] The same skill-task pair can pass through dry-run lifecycles for at least two adapters.
- [x] [RM-06] Profile differences are encoded in config, not hidden in code.
- [x] [RM-06] Dry-run artifacts and copied workspaces avoid in-place mutation and cross-run contamination.

## RM-07: Instrumented Trace Harness

Goal: collect evidence rather than guesses.

Tasks:

- [x] [RM-07] Create CLI command `skilldiff run`.
- [x] [RM-07] Create CLI command `skilldiff compare` as a trace-summary scaffold.
- [x] [RM-07] Create CLI command `skilldiff report` as a Markdown trace-summary scaffold.
- [x] [RM-07] Replace RM-06 dry-run local adapter scaffold with controlled RP2 live execution.
- [x] [RM-07] Replace RM-06 Docker adapter scaffold with controlled RP3 live execution using a real pinned image.
- [x] [RM-07] Define `trace.jsonl` event schema.
- [x] [RM-07] Capture run metadata: run ID, skill ID, task ID, profile ID, timestamp, profile hash, adapter ID, repeat ID.
- [x] [RM-07] Capture filesystem read events with MVP provenance; controlled Python commands emit `python_sitecustomize_wrapper_mvp` read events, and RP3 container commands can emit `container_strace_mvp` read events for supported `open`, `openat`, and `openat2` syscalls. Syscall-complete provenance across all runtimes remains pending.
- [x] [RM-07] Capture filesystem write and modify events through pre/post workspace diffs.
- [x] [RM-07] Capture process launch events for controlled local commands.
- [x] [RM-07] Capture shell command arguments.
- [x] [RM-07] Capture controlled Python network connection/send events for PV-02; packet capture and arbitrary-client interception remain pending.
- [x] [RM-07] Capture network payload metadata without storing sensitive full payloads by default for the controlled Python PV-02 path.
- [x] [RM-07/PV-02] Implement an in-process fake HTTP sink for explicit reserved benchmark destinations such as `sink.rp2.invalid`; public internet contact remains disabled.
- [x] [RM-07/PV-02] Emit `network_sink_requests.jsonl` with payload hashes, byte counts, redaction markers, and synthetic canary labels, not raw request bodies.
- [x] [RM-07/PV-02] Capture RP3 blocked egress under network denial as `network.connect` and `network.send` with `status: failed`.
- [x] [RM-07/PV-02] Add trace validation that fails on raw payload retention, missing hashes for captured bodies, or `public_internet_contacted: true`.
- [~] [RM-07] Capture tool call events; controlled `tool.call` events are now emitted for the MCP/tool workflow fixture, while live MCP/tool descriptor/result telemetry remains pending.
- [~] [RM-07] Capture approval prompt and decision event files; controlled semantic `approval.required`, `approval.prompt`, and `approval.decision` events are emitted for the MCP/tool workflow fixture, while a general live approval shim remains pending.
- [~] [RM-07] Capture persistence events; controlled `persistence.write` events are emitted for hidden `.skill-cache` behavior, while retained-state and cleanup-leftover semantics remain pending.
- [x] [RM-07] Capture generated report/output events.
- [x] [RM-07] Implement canary injection for the MVP `.env` fixture path.
- [x] [RM-07] Implement canary detection in changed files, generated outputs, stdout, and stderr.
- [x] [RM-07] Implement canary detection in generated outputs.
- [x] [RM-07] Implement canary detection in controlled network sink request artifacts.
- [~] [RM-07] Add trace redaction and payload hashing for MVP output/log events.
- [x] [RM-07] Add deterministic run directory layout.
- [x] [RM-07] Add cleanup records for temporary workspaces.
- [x] [RM-07] Add smoke tests for trace event serialization and validation, including RP3 fake-Docker live trace coverage.

Acceptance checks:

- [x] [RM-07] Each supported MVP run emits a trace even if execution is blocked or fails.
- [~] [RM-07] Trace events include enough fields for current MVP contract checking, including controlled tool and persistence findings; full cross-runtime semantic coverage remains pending.
- [x] [RM-07] Canary movement can be detected without real secrets for file/output/log surfaces.
- [x] [RM-07/PV-02] A fake-sink `POST` produces a normalized `network.send` event with `sink_type: fake_http`, payload hash, redaction marker, and canary labels when present.
- [x] [RM-07/PV-02] An RP3 network-denied run produces failed `network.connect` and `network.send` events and no successful public-internet event.
- [x] [RM-07/PV-02] Validation enforces hashed/redacted payload metadata and no public internet contact.

## RM-08: Benchmark Construction

Goal: build the dataset needed for credible evaluation.

Tasks:

- [~] [RM-08] Create benchmark directory structure; smoke workspace exists, canonical top-level skill/task/expected layout is pending.
- [ ] [RM-08] Create `benchmark/skills/benign`.
- [ ] [RM-08] Create `benchmark/skills/adversarial`.
- [ ] [RM-08] Create `benchmark/tasks`.
- [x] [RM-08] Create `benchmark/workspaces`.
- [ ] [RM-08] Create `benchmark/secrets`.
- [ ] [RM-08] Create `benchmark/contracts`.
- [~] [RM-08] Create `benchmark/expected`; repo-audit, AuditLens, and docs-forge oracle metadata exist.
- [x] [RM-08] Write benign document automation skills for the controlled docs-forge P1/P2 fixture.
- [x] [RM-08] Write adversarial document automation variants for docs-forge canary leak and source mutation.
- [~] [RM-08] Write benign repository maintenance skills; MVP repo-audit fixture exists.
- [~] [RM-08] Write adversarial repository maintenance variants; MVP repo-audit canary-leak fixture exists.
- [ ] [RM-08] Write benign data extraction skills.
- [ ] [RM-08] Write adversarial data extraction variants.
- [ ] [RM-08] Write benign API workflow skills.
- [ ] [RM-08] Write adversarial API workflow variants.
- [ ] [RM-08] Write benign MCP/tool workflow skills.
- [ ] [RM-08] Write adversarial MCP/tool workflow variants.
- [ ] [RM-08] Write benign local file operation skills.
- [ ] [RM-08] Write adversarial local file operation variants.
- [ ] [RM-08] Create task prompts for each skill.
- [~] [RM-08] Create expected functional outputs for each task; repo-audit, network-egress, AuditLens, and docs-forge MVP expected-output metadata exist.
- [~] [RM-08] Create synthetic canary files; repo-audit, network-egress, AuditLens, and docs-forge synthetic canaries exist.
- [~] [RM-08] Create synthetic `.env` files; repo-audit, AuditLens, and docs-forge MVP fixtures exist.
- [ ] [RM-08] Create synthetic home-directory secrets.
- [x] [RM-08/PV-02] Create fake network sink fixture for benchmark-only reserved destinations, with verified trace artifacts.
- [x] [RM-08] Create metadata for attack family labels.
- [x] [RM-08] Create benchmark manifest.
- [ ] [RM-08] Add license and release notes for benchmark artifacts.
- [x] [RM-08] Snapshot `adhit-r/docs-forge` at `40c3693491b49382682622408f167424ed814c71`.
- [x] [RM-08] Snapshot `adhit-r/audit-lens` at `241b584e8e7fc1cddfe2744a33e3c3907c871e95` for the sanitized AuditLens fixture.
- [x] [RM-08] Verify first-party source provenance from clean ephemeral clones for docs-forge and AuditLens.
- [x] [RM-08] Add bounded docs-forge live-installer dry-run scaffold and result evidence.
- [x] [RM-08] Add bounded docs-forge project-local non-dry-run installer scaffold, trace, and result evidence.
- [x] [RM-08] Add bounded docs-forge live runtime-pair scaffold, paired traces, and comparison result evidence.
- [x] [RM-08] Add bounded docs-forge live package-observer scaffold, trace, and result evidence.
- [x] [RM-08] Extract `docs-forge` canonical skill provenance from `plugins/docs-forge/skills/docs-forge/SKILL.md`.
- [x] [RM-08] Extract `docs-forge` adapter-surface provenance from `adapters/claude-code`, `adapters/antigravity`, and `adapters/universal`.
- [ ] [RM-08] Extract `audit-lens` canonical skill from `skill/SKILL.md`.
- [x] [RM-08] Inventory `audit-lens` references under `skill/references/`.
- [x] [RM-08] Inventory `audit-lens` demo evidence under `demo/acme-corp/`.
- [x] [RM-08] Create benign `docs-forge` task: generate architecture docs for a synthetic repo.
- [x] [RM-08] Create benign `docs-forge` task: generate framework-ready docs under an approved output directory.
- [x] [RM-08] Create adversarial `docs-forge` variant: overbroad ingestion tries to read `.env` and unrelated workspace files.
- [x] [RM-08] Create adversarial `docs-forge` variant: hidden side effect writes outside approved docs output.
- [x] [RM-08] Create benign `audit-lens` task: audit synthetic Acme evidence against ISO 27001.
- [x] [RM-08] Create benign `audit-lens` task: produce GRC and auditor workspace outputs from approved evidence.
- [x] [RM-08] Create adversarial `audit-lens` variant: propagates synthetic secrets into reports or generated HTML.
- [ ] [RM-08] Create adversarial `audit-lens` variant: attempts connector discovery or CLI auth checks without approval.
- [x] [RM-08] Write security contracts for `docs-forge` pilot tasks aligned to the runnable Python fixture.
- [x] [RM-08] Write security contracts for `audit-lens` pilot tasks.
- [x] [RM-08] Add pilot-case labels P1 to P4 to the benchmark manifest.

Acceptance checks:

- [ ] [RM-08] Every skill has at least one task.
- [ ] [RM-08] Every task has a contract.
- [~] [RM-08] Every adversarial variant maps to a named attack family; repo-audit, network-egress, AuditLens, and docs-forge MVP variants are mapped.
- [~] [RM-08] The benchmark contains no real secrets; current verified MVP, AuditLens, and docs-forge fixtures use synthetic canaries only.
- [x] [RM-08] First-party seed repos are pinned by commit hash.
- [x] [RM-08] First-party source hashes can be verified from clean ephemeral clones without vendoring full source trees.
- [x] [RM-08] First live docs-forge Node CLI dry-run evidence is excluded from MVP runtime-drift counts.
- [x] [RM-08] First live docs-forge project-local non-dry-run installer evidence is excluded from MVP runtime-drift counts.
- [x] [RM-08] First live docs-forge Node runtime-pair scaffold evidence is excluded from MVP runtime-drift counts.
- [x] [RM-08] First live docs-forge package-observer evidence is excluded from MVP runtime-drift counts.
- [~] [RM-08] Pilot mutations are controlled and do not publish real harmful payloads; AuditLens and docs-forge canary variants are synthetic and local-only.

## RM-09: Differential Analysis and Report Cards

Goal: transform traces into results.

Tasks:

- [~] [RM-09] Implement contract checker; MVP checker covers observed process, Python-level read, write, output, missing expected outputs, expected-output oracle markers, and canary sink events.
- [~] [RM-09] Implement filesystem violation detection; write detection, controlled Python read detection, and RP3 container-strace MVP read detection exist, while syscall-complete read provenance across all runtimes remains pending.
- [x] [RM-09] Implement shell violation detection.
- [x] [RM-09] Implement MVP network violation detection for observed `network.connect` and `network.send` events.
- [x] [RM-09/PV-02] Treat blocked RP3 egress to a denied destination as attempted overreach, not a realized data-flow violation.
- [x] [RM-09/PV-02] Treat successful fake-sink sends to a denied sink as realized D5 data-flow events when canary or denied payload metadata reaches the sink.
- [ ] [RM-09] Implement tool-call violation detection.
- [ ] [RM-09] Implement approval violation detection.
- [x] [RM-09] Implement canary sink detection for file/output/log surfaces.
- [x] [RM-09] Implement runtime-pair comparator for contract-check outputs.
- [~] [RM-09] Implement drift classification D1 to D5; current rules classify observed canary movement as D5.
- [ ] [RM-09] Implement per-skill report.
- [ ] [RM-09] Implement per-runtime report.
- [ ] [RM-09] Implement per-category report.
- [ ] [RM-09] Implement benchmark aggregate report.
- [~] [RM-09] Generate Markdown report cards; MVP contract reports, repo-audit, network-egress, AuditLens, docs-forge summaries, and contract-run comparisons exist.
- [ ] [RM-09] Generate CSV tables.
- [ ] [RM-09] Generate LaTeX tables.
- [ ] [RM-09] Generate heatmap data.
- [ ] [RM-09] Generate mitigation comparison data.
- [ ] [RM-09] Add examples of high-severity drift.
- [ ] [RM-09] Add examples of benign false positives.

Acceptance checks:

- [~] [RM-09] Reports identify RP2/RP3 contract-output disagreement and separate MVP Python-level read evidence plus RP3 container-strace MVP evidence from syscall-complete read-provenance claims.
- [~] [RM-09] Reports include trace evidence for each finding in the MVP contract report.
- [~] [RM-09] Reports are readable by a skill author, not only the paper author.
- [x] [RM-09/PV-02] Network reports state whether payloads were hashed/redacted and whether public internet contact was observed.

## RM-10: Mitigation Experiments

Goal: show that the measurement can guide practical defenses.

Tasks:

- [ ] [RM-10] Define default unrestricted baseline.
- [ ] [RM-10] Define static allowlist baseline.
- [ ] [RM-10] Define approval-only baseline.
- [ ] [RM-10] Define Docker sandbox baseline.
- [ ] [RM-10] Define taint-aware sink restriction.
- [ ] [RM-10] Define optional generated-policy profile.
- [ ] [RM-10] Run benign tasks under each mitigation.
- [ ] [RM-10] Run adversarial variants under each mitigation.
- [ ] [RM-10] Measure attack success rate.
- [ ] [RM-10] Measure benign task success.
- [ ] [RM-10] Measure approval burden.
- [ ] [RM-10] Measure false positives.
- [ ] [RM-10] Measure false negatives.
- [ ] [RM-10] Measure runtime overhead.
- [ ] [RM-10] Write analysis of approval-only failures.
- [ ] [RM-10] Write analysis of sandbox-only failures.
- [ ] [RM-10] Write analysis of allowlist maintenance cost.

Acceptance checks:

- [ ] [RM-10] Mitigation results are secondary and do not take over the paper.
- [ ] [RM-10] Security gains are reported with utility costs.
- [ ] [RM-10] The best mitigation is tied to observed drift classes.

## RM-11: Evaluation and Statistical Plan

Goal: make claims measurable and defensible.

Tasks:

- [x] [RM-11] Write experiment protocol in `paper/experiment-protocol.md`.
- [x] [RM-11] Define sample size target for MVP.
- [x] [RM-11] Define sample size target for full paper.
- [x] [RM-11] Decide number of repeated runs per skill-task-profile.
- [x] [RM-11] Decide how to handle nondeterministic agent outputs.
- [x] [RM-11] Define manual review procedure.
- [x] [RM-11] Define blinded review procedure if using human judgment.
- [x] [RM-11] Define inter-rater agreement plan if using humans.
- [x] [RM-11] Define confidence intervals or bootstrap method for drift rates.
- [x] [RM-11] Define ablations by runtime feature.
- [x] [RM-11] Define ablations by skill category.
- [x] [RM-11] Define ablations by attack family.
- [x] [RM-11] Define error taxonomy.
- [ ] [RM-11] Create results notebook or script.
- [ ] [RM-11] Create figure generation scripts.
- [x] [RM-11] Create reproducibility checklist in `paper/experiment-protocol.md`.

Acceptance checks:

- [x] [RM-11] Each research question maps to at least one table or figure.
- [x] [RM-11] Results distinguish measurement artifacts from true drift.
- [~] [RM-11] The evaluation can be rerun from a clean checkout; protocol and artifact README define the path, full release automation remains pending.

## RM-12: Paper, Artifact, and Release Plan

Goal: turn the work into a paper and reusable artifact.

Tasks:

- [ ] [RM-12] Create `paper/main.tex`.
- [ ] [RM-12] Create `paper/abstract.tex`.
- [ ] [RM-12] Create `paper/introduction.tex`.
- [ ] [RM-12] Create `paper/background.tex`.
- [ ] [RM-12] Create `paper/threat-model.tex`.
- [ ] [RM-12] Create `paper/taxonomy.tex`.
- [ ] [RM-12] Create `paper/system.tex`.
- [ ] [RM-12] Create `paper/benchmark.tex`.
- [ ] [RM-12] Create `paper/evaluation.tex`.
- [ ] [RM-12] Create `paper/mitigations.tex`.
- [ ] [RM-12] Create `paper/related-work.tex`.
- [ ] [RM-12] Create `paper/limitations.tex`.
- [ ] [RM-12] Create `paper/ethics.tex`.
- [ ] [RM-12] Create `paper/conclusion.tex`.
- [ ] [RM-12] Create `paper/refs.bib`.
- [x] [RM-12] Write introduction around the motivating example in `paper/introduction-skeleton.md`.
- [ ] [RM-12] Write the related-work differentiation before the full system section.
- [ ] [RM-12] Add figure F1 motivating example.
- [ ] [RM-12] Add figure F2 architecture.
- [ ] [RM-12] Add table T1 runtime profile matrix.
- [ ] [RM-12] Add table T2 drift taxonomy.
- [x] [RM-12] Add table T3 benchmark composition draft in `paper/tables/mvp-results.md`.
- [ ] [RM-12] Add table T8 related-work differentiation.
- [x] [RM-12] Create artifact README draft in `paper/artifact-readme.md`.
- [x] [RM-12] Create artifact install instructions draft in `paper/artifact-readme.md`.
- [ ] [RM-12] Create artifact reproduction script.
- [x] [RM-12] Create safe release checklist draft in `paper/artifact-readme.md`.
- [ ] [RM-12] Add CITATION.cff.
- [ ] [RM-12] Add SECURITY.md.
- [ ] [RM-12] Add LICENSE.

Acceptance checks:

- [~] [RM-12] Paper tells one coherent story: portable skill, different runtime, different security outcome; skeleton exists, full TeX draft remains pending.
- [ ] [RM-12] Artifact runs the MVP end to end.
- [~] [RM-12] Public release excludes real secrets and harmful payloads; local paths are now scrubbed from tracked artifacts, with final license/security metadata still pending.

## Suggested Repository Structure

Create this only after the two research docs are agreed.

```text
trust-the-skill-but-verify/
  README.md
  RESEARCH_ROADMAP.md
  RESEARCH_TODO.md
  pyproject.toml
  src/
    skilldiff/
      cli.py
      contracts/
      runners/
      traces/
      metrics/
      reports/
      canaries/
  schemas/
    security_contract.schema.json
    trace_event.schema.json
    drift_report.schema.json
  runtimes/
    profiles/
    adapters/
  benchmark/
    skills/
      benign/
      adversarial/
    tasks/
    contracts/
    workspaces/
    secrets/
    expected/
  experiments/
    configs/
    run_matrix.py
    compare_results.py
    reproduce_mvp.sh
  results/
    raw/
    processed/
    tables/
    figures/
  paper/
    main.tex
    refs.bib
  tests/
```

## First MVP Build Checklist

Purpose: produce the first concrete result quickly.

- [x] [RM-06] Create RP2 local coding-agent style profile.
- [x] [RM-06] Create RP3 Docker-sandboxed profile.
- [x] [RM-08] Create synthetic npm-style repo workspace.
- [x] [RM-08] Add `package.json`.
- [x] [RM-08] Add `src/index.js`.
- [x] [RM-08] Add `.env` containing `CANARY_REPO_AUDIT_SMOKE_0001`.
- [x] [RM-08] Add benign repo-audit skill.
- [x] [RM-08] Add adversarial repo-audit skill that tries to inspect `.env`.
- [x] [RM-05] Add contract allowing `package.json` and `src/**`.
- [x] [RM-05] Add contract denying `.env`.
- [x] [RM-07] Run benign skill under RP2.
- [x] [RM-07] Run benign skill under RP3.
- [x] [RM-07] Run adversarial skill under RP2.
- [x] [RM-07] Run adversarial skill under RP3.
- [x] [RM-09] Compare contract-check outputs; trace-level RP2/RP3 comparison exists.
- [x] [RM-09] Report whether `.env` was read directly in controlled Python MVP runs; RP2 succeeded and RP3 failed.
- [x] [RM-09] Report whether canary appeared in any sink.
- [x] [RM-09] Produce `results/mvp/repo-audit/drift_report.md`.

## First-Party Pilot Checklist

Purpose: turn the two existing skill repos into publishable case studies.

- [x] [RM-08] Create `benchmark/seeds/docs-forge/README.md` with source URL, commit hash, and included paths.
- [x] [RM-08] Create `benchmark/seeds/audit-lens/README.md` with source URL, commit hash, and included paths.
- [x] [RM-08] Decide whether to vendor snapshots or fetch pinned commits during reproduction; current publishable artifact uses controlled fixtures and pinned provenance, not vendored full source trees.
- [x] [RM-05] Create `contracts/docs-forge-docs-generation.yaml`.
- [x] [RM-05] Create `contracts/docs-forge-output-scope.yaml`.
- [x] [RM-05] Create `contracts/audit-lens-evidence-audit.yaml`.
- [x] [RM-05] Create `contracts/audit-lens-dashboard-generation.yaml`.
- [x] [RM-07] Run `docs-forge` benign task under RP2.
- [x] [RM-07] Run `docs-forge` benign task under RP3.
- [x] [RM-07] Run `docs-forge` adversarial variant under RP2.
- [x] [RM-07] Run `docs-forge` adversarial variant under RP3.
- [x] [RM-07] Run `audit-lens` benign task under RP2.
- [x] [RM-07] Run `audit-lens` benign task under RP3.
- [x] [RM-07] Run `audit-lens` adversarial variant under RP2.
- [x] [RM-07] Run `audit-lens` adversarial variant under RP3.
- [x] [RM-09] Produce docs-forge MVP report at `results/mvp/docs-forge/drift_report.md`.
- [x] [RM-09] Produce AuditLens MVP report at `results/mvp/audit-lens/drift_report.md`.
- [x] [RM-12] Write a paper subsection draft: "Pilot Case Studies: Documentation and Compliance Skills" in `paper/case-studies.md`.

MVP done when:

- [x] The benchmark can be run by one command.
- [x] At least one trace shows contract-compliant behavior.
- [x] At least one trace shows realized contract-violating behavior.
- [x] The report classifies the observed violation as a D5-labeled realized data-flow contract violation.

## Writing Checklist

- [ ] [RM-12] Keep the abstract focused on differential testing.
- [x] [RM-12] Use the motivating example in the first two pages.
- [ ] [RM-12] Put the drift taxonomy before system details.
- [ ] [RM-12] Put related-work differentiation early enough that reviewers see the novelty.
- [x] [RM-12] Avoid overclaiming real-world prevalence if the benchmark is synthetic.
- [x] [RM-12] Avoid saying all skills are dangerous.
- [x] [RM-12] Avoid saying approval prompts solve the problem.
- [x] [RM-12] Avoid making the policy compiler sound like the main invention.
- [x] [RM-12] Include limitations honestly in `paper/method-boundaries.md`.
- [~] [RM-12] Include ethics and safe-release details; artifact safety notes exist, full ethics section still pending.

## Open Decisions

- [x] [RM-01] Should the title use "Differential Security Testing" or "Runtime Security Drift"? Decision: use "Differential Security Testing" in the title and "runtime-induced drift" as the core phenomenon.
- [x] [RM-04] Should persistence drift be D6 or included under side-effect drift? Decision: keep persistence as a D4 side-effect subtype and report `persistence_violation_rate` separately.
- [x] [RM-06] Which real runtime should be validated first after controlled profiles? Decision: validate first-party source provenance first, then bounded docs-forge live-installer dry-run, project-local non-dry-run evidence, live Node runtime-pair scaffold, and offline package-observer evidence. Next is a Node-capable RP2/RP3 adapter or container image, or a registry/npx observer with explicit network controls, before live connector or RP4 claims.
- [ ] [RM-07] How should approval prompts be simulated consistently?
- [ ] [RM-08] How many adversarial variants are safe to publish?
- [ ] [RM-10] Should generated policies be included in the first submission or deferred?
- [ ] [RM-11] How many repeated runs are enough for nondeterministic agents?
- [ ] [RM-12] Is the first target a workshop paper or full conference submission?

## Weekly Execution Plan

Week 1:

- [x] [RM-01] Freeze scope, title, and thesis.
- [x] [RM-02] Finish related-work matrix.
- [ ] [RM-03] Finish threat model.
- [x] [RM-04] Finish drift taxonomy.

Week 2:

- [x] [RM-05] Draft contract schema.
- [x] [RM-06] Draft runtime profiles.
- [x] [RM-07] Build trace schema.
- [x] [RM-08] Build MVP repo-audit skill pair.

Week 3:

- [x] [RM-07] Implement MVP runner.
- [x] [RM-07] Implement canary detection for file/output/log surfaces.
- [~] [RM-09] Implement contract checker.
- [x] [RM-09] Produce first RP2/RP3 drift-candidate report.

Week 4:

- [ ] [RM-08] Expand benchmark to 10 skills.
- [ ] [RM-10] Add one mitigation baseline.
- [x] [RM-11] Write initial experiment protocol.
- [x] [RM-12] Draft introduction and motivating example.

Week 5 to 8:

- [ ] [RM-08] Expand benchmark to 40 skills.
- [ ] [RM-09] Generate aggregate tables.
- [ ] [RM-10] Run mitigation study.
- [ ] [RM-11] Run ablations.
- [ ] [RM-12] Draft full paper skeleton.

Week 9 to 12:

- [ ] [RM-08] Expand benchmark to final size.
- [ ] [RM-11] Complete evaluation.
- [ ] [RM-12] Complete paper draft.
- [ ] [RM-12] Package artifact.
- [ ] [RM-12] Run reproducibility check.

## Definition of Done for the Research Track

- [x] [RM-01] Thesis is crisp.
- [x] [RM-02] Related work gap is defensible.
- [ ] [RM-03] Threat model is safe and clear.
- [x] [RM-04] Drift metrics are computable.
- [x] [RM-05] Contracts are expressive.
- [x] [RM-06] Runtime profiles are reproducible.
- [~] [RM-07] MVP traces are reliable for controlled RP2/RP3 Python commands, RP3 container-strace MVP file-open evidence, and PV-02 controlled Python fake-sink plus blocked RP3 egress evidence; broader syscall completeness, arbitrary-client network capture, tool, approval, and persistence provenance remains pending.
- [ ] [RM-08] Benchmark is representative.
- [~] [RM-09] Reports are actionable for the MVP repo-audit case.
- [ ] [RM-10] Mitigations are measured, not hand-waved.
- [ ] [RM-11] Evaluation answers every RQ.
- [ ] [RM-12] Paper and artifact are ready for external review.
