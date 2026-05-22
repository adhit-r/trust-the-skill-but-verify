# Paper Spine

This file is the current top-tier full-paper spine. It freezes the argument
the rest of the repository should build toward. The paper target is not a
workshop, short paper, demo, or technical report. The only goal is a full
systems-security paper for NDSS, USENIX Security, IEEE S&P, ACM CCS, or an
equivalent venue.

## Working Title

**Trust the Skill, Verify the Runtime: Differential Security Testing for
Portable AI Agent Skills**

## Primary Abstract

Portable AI-agent skills are increasingly shared across hosted assistants,
local coding agents, plugin runtimes, and MCP-connected clients. Existing work
largely treats a skill as the security object: scan the package, identify
malicious instructions, infer least-privilege actions, or compile the skill
across frameworks. This misses a critical portability boundary. The same
skill, task, and instruction text can execute with different filesystem scope,
network policy, approval mediation, tool exposure, and persistence semantics
depending on the runtime that loads it.

This paper introduces differential runtime security testing for portable agent
skills. The method fixes a skill, task, workspace, task-conditioned security
contract, adversarial variant, and repeat identity, then varies the runtime
profile. Each run emits normalized traces over file, process, network, output,
canary-flow, and, in the full paper, activation, approval, tool/MCP, cleanup,
and persistence events. Contract checking separates realized violations,
attempted overreach, missing expected outputs, oracle failures, and
runtime-pair disagreements.

The current evidence package demonstrates feasibility across controlled
repository-audit, network-egress, compliance-audit, and document-automation
case families, with pinned provenance, scrubbed artifacts, CI validation, and
machine-checked claim references. The full paper will scale this into a
top-tier benchmark with at least 40 skills, 120 skill-task-contract runs before
repeats, four or more runtime profiles, repeat-run statistics, manual
adjudication, and mitigation report cards. The central claim is that skill
security portability is a runtime-conformance problem: a portable skill is not
secure merely because its artifact is unchanged; it is secure only when host
runtimes preserve the task-conditioned security contract under execution.

## Paper Thesis

Security behavior for portable agent skills is an emergent property of the
skill artifact, user task, workspace, contract, runtime profile, exposed tools,
approval policy, and persistence boundary. Therefore, evaluating skill security
requires differential execution across runtimes, not only static inspection of
the skill package.

## Final Research Questions

| ID | Research Question | Current Evidence State | Full-Paper Gate |
| --- | --- | --- | --- |
| RQ1 | How often does a skill's security behavior change across runtime profiles when skill, task, workspace, contract, variant, prompt hash, and repeat ID are fixed? | Supported for RP2/RP3 baseline evidence. | Report runtime-pair disagreement rates over at least 120 skill-task-contract runs before repeats. |
| RQ2 | Which runtime profile features are associated with realized violations, attempted overreach, missing outputs, and canary movement? | Partially supported for filesystem and network policy. | Add feature-level ablations across filesystem, shell, network, approval, tool/MCP, and persistence controls. |
| RQ3 | Do activation and skill-selection surfaces produce security-relevant drift across hosts? | Not yet answered. | Add activation events and activation-negative-control fixtures. |
| RQ4 | Can task-conditioned security contracts classify unsafe behavior without collapsing blocked attempts into realized violations? | Supported for the current RP2/RP3 contract evidence. | Validate across the scaled benchmark with manual adjudication for semantic findings. |
| RQ5 | Are approval prompts and tool/MCP mediation sufficient to preserve task-conditioned security contracts? | Not yet answered. | Add deterministic approval shims and controlled MCP/tool workflows. |
| RQ6 | Which mitigations reduce runtime-induced drift while preserving task utility? | Not yet answered. | Add RP6 hardened profile, least-privilege baseline, ablations, and report cards. |

Primary RQ: RQ1 is the paper's main measurement question. RQ2-RQ6 explain
causes, coverage, validation, tool/approval boundaries, and mitigations.

## Contributions

1. A formal framing of runtime-induced security drift for portable agent skills.
2. A task-conditioned security contract model for defining allowed and denied
   reads, writes, commands, network sinks, tool calls, approvals, outputs, and
   canary flows.
3. A normalized trace schema and differential comparator that hold skill, task,
   contract, prompt, workspace, variant, and repeat invariants fixed across
   runtime pairs.
4. A benchmark methodology for benign and adversarial skill-task-contract
   triples with synthetic canaries, source provenance, and safe publication
   boundaries.
5. A scaled empirical study target of at least 40 skills and 120
   skill-task-contract runs before repeats across four or more runtime
   profiles.
6. A rigor layer with repeats, utility metrics, uncertainty estimates, manual
   adjudication, and two-reviewer agreement.
7. Mitigation report cards that compare hardened runtime profiles and
   least-privilege-style baselines by drift reduction and utility cost.

## Threat Model

Assets:

- User workspaces, repository files, source fixtures, generated reports,
  synthetic secrets, synthetic canaries, tool descriptors, connector-like
  resources, and persistent runtime state.

Trusted components:

- The benchmark harness, tracked task prompts, tracked contracts, tracked
  expected-output metadata, pinned source-provenance manifests, and CI
  verification scripts are trusted to define the experimental boundary.

Runtime under test:

- Each runtime profile is treated as an implementation of a host security
  boundary. The runtime may expose different filesystem roots, shell access,
  network policy, approval behavior, MCP/tool access, and persistence.

Benign skill assumption:

- A benign skill attempts to complete the user task using only contract-allowed
  sources, sinks, commands, tools, and outputs.

Adversarial skill assumption:

- An adversarial variant may attempt overbroad reads, canary propagation,
  source mutation, hidden persistence, network egress, approval bypass, tool
  overreach, or activation overreach. The adversary is bounded to the
  benchmark task and synthetic fixtures; it does not target real credentials or
  public internet services.

Attacker capabilities:

- The attacker can control skill instructions, bundled helper code, examples,
  templates, activation text, and adversarial task variants used in the
  benchmark.
- The attacker can attempt to read synthetic secret files, write outside
  approved output locations, invoke denied commands, send controlled fake-sink
  network requests, include canaries in outputs, or retain hidden state.
- The attacker can exploit permissive runtime policy but cannot break out of
  the host operating system, compromise GitHub Actions, modify tracked
  manifests after validation, or access real user credentials.

Non-goals:

- Measuring ecosystem prevalence.
- Claiming any single runtime is universally safe.
- Testing public-internet exfiltration.
- Evaluating real customer data, real connector credentials, or live SaaS
  exports.
- Providing syscall-complete tracing for every host.
- Proving full product behavior for first-party seed repositories unless the
  paper explicitly labels that execution level.

Safety boundary:

- All publishable secrets are synthetic canaries. Raw payloads, local absolute
  paths, real credentials, auth state, cookies, live SaaS exports, and customer
  data are outside the artifact boundary.

## Related-Work Differentiation

| Line Of Work | Closest Examples | Difference From This Paper |
| --- | --- | --- |
| Skill vulnerability and malicious-skill measurement | Agent Skills in the Wild; Malicious Agent Skills in the Wild; HarmfulSkillBench | Those works classify skills or malicious skill behavior. This paper fixes the skill-task-contract triple and varies the runtime to measure security conformance drift. |
| Skill-file prompt injection and registry manipulation | Skill-Inject; Under the Hood of SKILL.md | Those works study compromised skill text, discovery, selection, and governance. This paper starts after selection and asks whether runtime execution preserves security semantics. |
| Task-conditioned least privilege | SkillScope and related policy-constraining work | Least privilege is a baseline or mitigation here, not the main measurement question. The independent variable is runtime profile disagreement. |
| Cross-framework skill compilation | SkCC and skill intermediate-representation work | Compilation improves functional portability before execution. This paper tests security behavior after deployment under different host policies. |
| MCP and tool security | MCP protocol and tool-poisoning studies; ClawGuard-style guardrails | Those works focus on descriptors, authorization, client validation, and tool-call boundaries. This paper uses MCP/tool surfaces as runtime-profile dimensions and measures drift with controlled skill and tool conditions. |
| Agent prompt-injection benchmarks | AgentDojo, InjecAgent, and related tool-agent benchmarks | Those works evaluate attack success and defenses in tool-using agents. This paper's unit is runtime-pair conformance for portable skills. |

Reviewer-facing differentiation sentence:

> This paper is not another skill scanner, malicious-skill corpus,
> least-privilege compiler, or MCP-only defense. It is a differential
> conformance test for the runtime boundary that makes skill portability
> security-relevant.

## Reviewer-Risk Table

| Reviewer Objection | Risk | Evidence Answer Or Required Work |
| --- | --- | --- |
| "This is just another skill-safety benchmark." | Critical | Lead with runtime-pair conformance as the unit of analysis. Keep attack success secondary to cross-runtime disagreement under fixed invariants. |
| "Four current case families are too small." | Critical | Treat current evidence as feasibility only. Full-paper gate remains 40+ skills and 120+ runs before repeats. |
| "RP2/RP3 is not enough runtime diversity." | Critical | Add at least two more executable profiles or justify an equivalent-depth full-paper scope with deeper instrumentation and mitigations. |
| "Controlled Python fixtures are artificial." | High | Add full-product or partial real-execution slices and label every evidence level as full product, controlled fixture, or source-only. |
| "Instrumentation gaps look like false security." | High | Add activation, approval, tool/MCP, persistence, and capability-snapshot events. Count missing observers as instrumentation gaps, not security success. |
| "No nondeterminism treatment." | High | Add repeat IDs, three deterministic repeats where promoted, five repeats for model-mediated cases, and per-repeat tables. |
| "No human validation for semantic findings." | High | Add adjudication forms, blinded sample review, percent agreement, and Cohen's kappa when label counts support it. |
| "No baseline or mitigation." | High | Add RP6 hardened profile, least-privilege-style baseline, and ablations over runtime controls. |
| "Artifact may leak private data." | High | Keep CI path-scrub, synthetic-only canaries, no public internet contact, no real secrets, and anonymous artifact checklist. |
| "Why not just use least privilege?" | Medium | Position least privilege as one mitigation baseline; the paper measures whether runtimes preserve contracts before and after mitigation. |
| "Docker blocks more but hurts utility." | Medium | Report missing outputs and benign task success beside realized violations and attempted overreach. |
| "Venue reviewers will reject vague claims." | Medium | Every numerical claim must map to the claim ledger, result artifacts, manifests, or protocol text. |

## Venue Backplan

As of 2026-05-23, the top-tier target plan is:

| Target | Role | Paper-State Requirement |
| --- | --- | --- |
| NDSS 2027 Fall deadline, August 19, 2026 | Aggressive target | P0-P5 complete by late July 2026, with at least four profiles or equivalent-depth justification. |
| IEEE S&P 2027 second deadline, November 17, 2026 | Strong target | P0-P6 mature by October 2026, including mitigation/report-card evidence. |
| USENIX Security 2027 Cycle 2 deadline, January 26, 2027 | Primary realistic target | Full benchmark, statistics, mitigations, artifact, anonymity, and manuscript complete by early January 2027. |
| ACM CCS next full cycle | Backup top-tier target | Use only if the full evidence package is ready and the paper is clearly differentiated from skill-safety benchmark work. |

Venue choice is a paper-readiness decision, not a scope-reduction decision. If
the evidence does not meet the full-paper gate for the earliest venue, the work
moves to the next top-tier deadline rather than downshifting to a workshop or
short-paper target.

Official venue sources checked on 2026-05-23:

- NDSS 2027 call for papers:
  `https://www.ndss-symposium.org/ndss2027/submissions/call-for-papers/`
- IEEE S&P 2027 call for papers:
  `https://sp2027.ieee-security.org/cfpapers.html`
- USENIX Security 2027:
  `https://www.usenix.org/conference/usenixsecurity27`
- ACM CCS 2026 call for papers and artifact policy:
  `https://www.sigsac.org/ccs/CCS2026/call-for/call-for-papers.html`

## Immediate Writing Order

1. Rewrite the introduction around "runtime as the security variable."
2. Move this threat model into the main manuscript.
3. Convert the related-work differentiation into a paper section with
   primary-source citations.
4. Expand the current result tables only after P2/P3/P4 evidence gates improve.
5. Add figures for architecture, trace lifecycle, runtime profile matrix,
   drift outcomes, mitigation report cards, and artifact flow.
