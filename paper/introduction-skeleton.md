# Introduction Skeleton

Working title:

**Trust the Skill, Verify the Runtime: Differential Security Testing for
Portable AI Agent Skills**

## Opening Problem

AI agent skills are becoming portable software artifacts. A skill can combine
natural-language operating instructions, activation metadata, scripts,
templates, examples, dependencies, and tool-use procedures, then move across
hosted assistants, local coding agents, plugin systems, and MCP-connected
clients. That portability is usually treated as a packaging problem: if the
skill installs and the instructions transfer, the skill is considered portable.

Security does not move that cleanly. A skill's effective behavior depends on
the runtime that loads it: which files are mounted, whether shell commands are
available, whether network egress is blocked, whether approval prompts reveal
the sensitive target, whether tools and MCP resources are exposed, and whether
state persists after the task. The same skill text can therefore become a
different security object when moved from one runtime to another.

Core claim:

> Skill portability is a security-conformance problem, not only a syntax or
> packaging problem.

## Motivating Example

Use the repo-audit MVP as the first-page example.

Setup:

- Skill: `repo-audit-executable`
- Task: generate a dependency audit report.
- Contract: read package metadata and write `reports/audit.md`; do not read or
  propagate `.env`.
- Canary: `CANARY_REPO_AUDIT_SMOKE_0001`, synthetic and safe to publish.
- Runtime pair: RP2 local coding-agent profile and RP3 Docker-sandbox profile.

Observed behavior:

- Benign RP2 and RP3 runs complete without canary movement.
- Adversarial RP2 reads `.env` and leaks the canary into the local report.
- Adversarial RP3 records a failed `.env` read and fails closed before canary
  movement.

Point to make:

The skill, task, and contract are fixed. The outcome changes because the
runtime profile changes. That is the phenomenon the paper measures.

## Why Existing Framings Are Insufficient

Static scanning asks whether a skill looks vulnerable or malicious. That is
useful, but it does not answer whether a host will expose `.env`, block network
egress, require approval, or persist hidden state during execution.

Least-privilege enforcement asks whether a skill can be constrained to the
minimum actions needed for a task. That is also useful, but it is a mitigation
and policy-design question. It does not measure whether two runtimes enforce
comparable security semantics for the same skill.

Skill compilation asks whether a skill can be translated across frameworks
without losing functional intent. That still leaves the runtime boundary open:
two hosts may receive equivalent skill artifacts but grant different
filesystem, shell, network, tool, approval, and persistence authority.

MCP and tool-security work studies poisoned descriptors, trust propagation,
client validation, authorization, and tool-specific attacks. This paper uses
that line of work to define runtime profiles, but the central experiment holds
the skill and task constant and varies the host policy.

## Research Question

Main question:

> When the same portable skill is executed under different runtime profiles,
> does its task-conditioned security behavior remain stable?

Operational version:

> Given a skill, task, contract, runtime profile, and trace, can we detect
> whether unsafe behavior is realized, blocked, converted into missing output,
> or observed as canary movement?

## Contributions

1. Runtime-induced drift taxonomy for portable skill security, covering
   activation, privilege, approval, side-effect, and data-flow drift.
2. Differential testing harness that executes the same skill-task-contract
   triple across runtime profiles and emits normalized traces.
3. Task-conditioned security contracts that define allowed reads, writes,
   commands, sinks, expected outputs, and approval requirements.
4. Controlled benchmark methodology with benign tasks, adversarial variants,
   synthetic canaries, expected outputs, and safe publication boundaries.
5. MVP evidence over four case families showing five runtime-drift claims
   across RP2 and RP3, with explicit provenance and measurement limits.

## Pilot Results Paragraph

The current MVP evaluates four controlled case families: repo-audit,
network-egress, AuditLens P3/P4, and docs-forge P1/P2. Across these cases,
tracked manifests record five runtime-drift claims and twenty-four pairwise
disagreements under RP2 and RP3. The evidence includes RP2 canary movement into
generated reports or dashboards, RP3 blocked attempts, missing outputs,
read-only source-mount failures, and controlled fake-sink network evidence.
These results are not prevalence claims; the controlled MVP traces demonstrate
measurable runtime-conditioned differences and show that differential traces
can separate realized violations from blocked overreach and utility failures.

## Scope And Nonclaims

This paper does not claim:

- all skills are unsafe,
- Docker prevents every unsafe behavior,
- approval prompts solve skill security,
- the harness is syscall-complete,
- docs-forge Node installer behavior was fully evaluated,
- AuditLens live connector behavior was evaluated,
- public-internet egress was tested.

Use the current paper line:

> We measure runtime security conformance for portable skills. We do not infer
> global ecosystem prevalence from the MVP.

## Section Flow

1. Introduction and motivating repo-audit example.
2. Background on portable skills, runtimes, and security contracts.
3. Threat model and safe synthetic-secret policy.
4. Drift taxonomy and metrics.
5. Differential testing framework.
6. Benchmark construction and first-party seed cases.
7. Runtime profiles and trace instrumentation.
8. Evaluation over RP2/RP3 and expanded profiles.
9. Mitigation study.
10. Related work.
11. Limitations, ethics, and responsible release.

## Writing Notes

- Lead with the repo-audit example before discussing architecture.
- Put the drift taxonomy before system implementation details.
- Introduce related work early enough that the contribution is not mistaken for
  a scanner, least-privilege compiler, or MCP-only paper.
- Keep policy compilation secondary; the main contribution is differential
  testing.
- Preserve the measured wording: realized violation, attempted overreach,
  missing output, oracle failure, canary observation, and runtime-pair
  disagreement.
