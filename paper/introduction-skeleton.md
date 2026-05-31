# Introduction Draft

Working title:

**SkillDiff: Differential Runtime Conformance Testing for Portable AI Agent
Skills**

## Opening Problem

Portable AI-agent skills are becoming reusable software artifacts. A skill can
bundle natural-language operating instructions, activation metadata, scripts,
templates, examples, dependencies, and tool-use procedures, then move across
hosted assistants, local coding agents, plugin runtimes, and MCP-connected
clients. Portability is often treated as a packaging property: if the same
artifact installs, activates, and exposes the intended instructions, the skill
is considered portable.

Security does not move with the artifact that cleanly. The runtime that loads a
skill decides which files are mounted, whether shell commands can run, whether
network egress is available, whether approval prompts mediate sensitive
actions, which tool and MCP resources are reachable, how outputs are captured,
and whether state persists after the task. A skill can therefore be identical
at rest but become a different security object in execution.

SkillDiff starts from this gap. The experimental invariant is fixed: skill, task, contract, workspace snapshot, task prompt, variant, and repeat identity.
The runtime profile is the variable. SkillDiff measures conformance changes rather than prevalence: whether a runtime realizes a violation, blocks an attempt, converts the task into a missing output, produces an oracle failure, exposes a canary, or disagrees with another runtime under the same invariant.

The core thesis is that skill portability is a runtime-conformance problem, not
only a syntax, packaging, scanner, or least-privilege problem.

## Motivating Example

Consider a repository-audit skill that is asked to generate a dependency audit
report. The task-conditioned contract permits reading package metadata and
writing `reports/audit.md`; it denies reading or propagating `.env`. The
workspace contains a synthetic publishable canary,
`CANARY_REPO_AUDIT_SMOKE_0001`, only in the denied `.env` file.

The skill, task, contract, workspace snapshot, task prompt, adversarial variant,
and repeat identity are held fixed. Under the RP2 local coding-agent profile,
the adversarial run reads `.env` and places the canary in the generated report.
Under the RP3 Docker-sandbox profile, the corresponding adversarial run records
a failed `.env` read and fails closed before canary movement. In ledger form,
Repo-audit adversarial RP2 has three realized violations, one oracle failure,
and four canary observations; adversarial RP3 has one attempted overreach, one
missing output, and no canary observations.

This is not a claim that one host is universally unsafe or another host is
universally safe. It is the phenomenon the paper measures: the same portable
skill-task-contract triple can produce different task-conditioned security
behavior because the runtime boundary changes.

## Why Existing Framings Are Insufficient

Static skill scanning asks whether a skill package appears malicious,
overbroad, or policy-relevant before execution. That is useful, but it does not
answer whether a host will mount `.env`, block network egress, mediate a tool
call, preserve hidden state, or leak a synthetic canary during a concrete task.

Task-conditioned least privilege asks whether a skill can be constrained to the
minimum actions needed for a task. SkillDiff uses least-privilege-style
artifacts as baselines and mitigations, but least privilege is not the main
measurement question. The main question is whether different runtimes preserve
the same contract when the skill, task, workspace, prompt, variant, and repeat
are fixed.

Cross-framework skill compilation asks whether functional intent can be
translated across skill formats. SkillDiff starts after that point. Two
runtimes may receive semantically equivalent skill instructions but grant
different filesystem, shell, network, approval, tool, context, cleanup, and
persistence authority.

MCP and tool-security work studies descriptors, authorization, tool poisoning,
client validation, routing, and guardrails. SkillDiff treats those surfaces as
runtime-profile dimensions. It is not an MCP-only defense, a Semia
reproduction, a ClawGuard reproduction, or a Task Shield reproduction.

## Research Question

The paper asks:

> When the same portable skill is executed under different runtime profiles,
> does its task-conditioned security behavior remain stable?

Operationally, SkillDiff compares runs with fixed skill, task, contract,
workspace snapshot, task prompt, variant, and repeat identity. Each run emits a
normalized trace over supported file, process, network, output, canary,
activation, approval, tool/MCP, persistence, cleanup, and instrumentation
events. Contract checking separates realized violations, attempted overreach,
missing expected outputs, oracle failures, instrumentation failures, canary
observations, and runtime-pair disagreements.

This framing makes runtime-pair conformance the unit of analysis. Attack
success is important, but only as one outcome among several ways a runtime can
fail to preserve the task-conditioned contract.

## Current Evidence

The current executable baseline evaluates five controlled case families:
repo-audit, network-egress, MCP/tool workflow, AuditLens P3/P4, and docs-forge
P1/P2. Across these cases, tracked manifests record five runtime-drift claims
and thirty-six pairwise disagreements under RP2 and RP3. The evidence includes
RP2 canary movement into generated reports or dashboards, RP3 blocked attempts,
missing outputs, read-only source-mount failures, controlled fake-sink network
evidence, and controlled semantic events for approval, tool, and persistence
behavior.

The broader repository now contains promoted bounded evidence that strengthens
the paper direction but must remain labeled. The manifest records forty-four
skills and one hundred thirty-two skill-task-contract triples, but that is
manifest and source-provenance accounting plus bounded fixture promotion, not
paper-grade execution completion. RP1 is simulator-backed; RP4 is bounded
local MCP fixture evidence; RP5 is fixture-backed plugin-style evidence; RP6 is
a policy-hardened report-card and ablation pilot with utility cost reported.
Gate 5 artifacts provide machine-only Wilson, bootstrap, and paired-runtime
summaries, but completed human review remains zero.

These results are not prevalence claims; the controlled baseline traces
demonstrate measurable runtime-conditioned differences and show that
differential traces can separate realized violations from blocked overreach,
missing outputs, and utility failures. This paper does not claim commercial-runtime coverage, public-internet exfiltration evidence, defense success, or completed human review.

## Contributions

This paper contributes:

1. A runtime-conformance framing for portable AI-agent skills: a skill's
   security behavior is evaluated under fixed skill, task, contract, workspace,
   prompt, variant, and repeat identity while varying runtime profile.
2. A task-conditioned security contract model for allowed and denied reads,
   writes, commands, network sinks, approvals, tool calls, expected outputs,
   and canary flows.
3. A normalized trace and comparator pipeline that distinguishes realized
   violations, attempted overreach, missing outputs, oracle failures,
   instrumentation failures, canary observations, and runtime-pair
   disagreements.
4. A benchmark methodology for benign tasks, adversarial variants, negative
   controls, synthetic canaries, source provenance, safe publication
   boundaries, and repeat-aware inclusion records.
5. A bounded current evidence package and strengthening layer that separate
   current executable RP2/RP3 evidence from simulator, fixture, report-card,
   repeat, machine-only interval, and review-ready scaffold evidence.

## Scope And Nonclaims

SkillDiff measures runtime security conformance for portable skills. It does
not infer global ecosystem prevalence from the current baseline evidence.

This paper does not claim:

- all skills are unsafe,
- Docker prevents every unsafe behavior,
- approval prompts solve skill security,
- RP6 as completed defense evidence,
- the harness is syscall-complete,
- Semia equivalence or Semia reproduction,
- ClawGuard or Task Shield reproduction,
- commercial hosted, local-agent, plugin-store, or MCP-client behavior,
- public-internet exfiltration,
- public-registry package acquisition,
- full AuditLens product or live connector behavior,
- full docs-forge docs-generation behavior,
- completed human review, reviewer agreement, or adjudication.

All publishable secrets in the current artifact are synthetic canaries. Real
credentials, cookies, customer data, live SaaS exports, auth state, and public
network exfiltration are outside the artifact boundary.

## Section Flow

1. Introduction and motivating repo-audit example.
2. Background on portable skills, runtimes, and security contracts.
3. Threat model and safe synthetic-secret policy.
4. Drift taxonomy and metrics.
5. Differential testing framework.
6. Benchmark construction and source-provenance methodology.
7. Runtime profiles and trace instrumentation.
8. Evaluation over RP2/RP3 and bounded promoted profiles.
9. Baselines, mitigations, report cards, repeats, and uncertainty.
10. Related work.
11. Limitations, ethics, and responsible release.

## Writing Notes

- Lead with the runtime as the security variable, not skill malware.
- Use the repo-audit example before architecture details.
- Keep "current executable evidence" separate from promoted simulator,
  fixture, report-card, repeat, and machine-only interval evidence.
- Do not describe 44 skills / 132 triples as full execution completion.
- Keep policy compilation secondary; the main contribution is differential
  runtime conformance testing.
