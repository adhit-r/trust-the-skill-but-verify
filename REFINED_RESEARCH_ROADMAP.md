# Refined Research Roadmap

This roadmap converts the current pilot into a submission-grade security
measurement paper. It preserves the existing project framing but tightens
priorities around evidence integrity, runtime comparability, instrumentation
coverage, scale, and artifact readiness.

## North Star

Build and evaluate a differential security testing framework for portable AI
agent skills. The paper should show that security behavior is not determined by
the skill artifact alone; it emerges from the interaction among skill
instructions, task context, runtime policy, tool exposure, approvals,
filesystem scope, network policy, and persistence.

The full-paper claim should be:

> Given a fixed skill, task, workspace, and task-conditioned security contract,
> different agent runtime profiles can produce measurably different security
> outcomes. These outcomes can be captured through normalized traces, classified
> through contracts, and summarized as security conformance report cards.

## P0: Evidence Integrity Gate

Goal: make the existing MVP evidence reliable, rerunnable, and safe before
adding more cases.

Why this is first: top-tier reviewers punish artifact drift. Current evidence is
useful, but source hashes, path scrubbing, comparator invariants, and normalized
blocked-write evidence need to be tightened.

Milestone outputs:

- Reproduction scripts verify pinned source hashes before running first-party
  fixtures.
- Sanitization is integrated into generation/reproduction, not only applied
  after the fact.
- Comparator refuses to classify runtime drift unless skill, task, contract,
  prompt, workspace, variant, and repeat invariants match.
- RP3 blocked source mutations emit normalized attempted write events.
- CI runs schema validation, trace validation, contract checks, JSON checks,
  and no-local-path checks.

Acceptance gate:

- A clean checkout can regenerate the current MVP tables without local path
  leakage or manual patching.

## P1: Claim Contract And Paper Spine

Goal: lock exactly what the paper claims and what it does not claim.

Milestone outputs:

- Final RQ list with one primary RQ: runtime conformance drift.
- Threat model with in-scope and out-of-scope attacker capabilities.
- Paper contribution list that separates method, artifact, benchmark, and
  measurement.
- Related-work matrix updated for May 2026 skill-security papers.
- Reviewer-risk table mapping every likely objection to evidence or limitation
  wording.

Acceptance gate:

- Every number and claim in the intro skeleton points to a table, manifest, or
  experiment protocol item.

## P2: Instrumentation Coverage Expansion

Goal: make the D1-D5 taxonomy real across more than file/network/output traces.

Priority instrumentation:

1. Activation events for discovery, selection, activation, and non-activation.
2. Approval events for requested, decision, bypassed, and not-required actions.
3. Tool/MCP events for tool calls, descriptor reads, arguments, results, and
   mutations.
4. Persistence events for hidden files, caches, memory, retained state, and
   cleanup leftovers.
5. Runtime capability snapshots for available privilege, not just exercised
   privilege.

Milestone outputs:

- Event schema updates and validators.
- Adapter support matrix per profile.
- At least one executable case for D1, D3, tool/MCP, and persistence.
- Instrumentation-status files that fail validation when declared observers are
  unavailable.

Acceptance gate:

- The project can honestly say it measures all five drift classes in at least
  one executable case family, while still reporting per-surface limitations.

## P3: Runtime Profile Expansion

Goal: move beyond RP2/RP3 and show the method applies to realistic host
families.

Priority profiles:

| Profile | Role | Minimum Evidence |
| --- | --- | --- |
| RP1 restricted hosted-style | Narrow file scope, strong approvals, limited shell | Simulator or adapter with explicit unsupported surfaces. |
| RP2 local coding-agent | Broad local workspace and shell | Already active; add approval/tool/persistence events. |
| RP3 Docker sandbox | Explicit mounts and network controls | Already active; add blocked-write normalization and more clients. |
| RP4 MCP-connected | Tool and resource server exposure | At least one controlled MCP/tool workflow. |
| RP5 plugin-style | Skill/package activation and install/update behavior | At least one activation and install-surface case. |
| RP6 policy-hardened | Mitigation profile | A hardened comparison against RP2/RP3 for report cards. |

Acceptance gate:

- At least three profiles are executable for the short-paper target.
- At least four profiles are executable for the full-paper target, or the paper
  narrows claims to profiles actually evaluated.

## P4: Benchmark Expansion

Goal: turn pilot cases into a benchmark with enough breadth for quantitative
claims.

Short-paper target:

- At least 10 skills.
- At least 30 skill-task-contract triples.
- 2-3 runtime profiles.
- 3 repeats for deterministic fixtures where useful.
- 5 repeats for model-mediated or nondeterministic agent runs.

Full-paper target:

- At least 40 skills.
- At least 120 skill-task-contract runs.
- 3-6 runtime profiles.
- Benign and adversarial variants.
- Categories: document automation, repository maintenance, compliance audit,
  network/API workflow, MCP/tool workflow, local file operation, and persistence.

Acceptance gate:

- The paper can report category-level and runtime-pair-level metrics without
  relying on only the original four pilot families.

## P5: Experimental Rigor And Statistics

Goal: make the evaluation legible to systems-security reviewers.

Milestone outputs:

- Stable train/dev/test or pilot/paper split for cases.
- Repeat-run records with fixed seeds or recorded model/runtime parameters.
- Manual adjudication protocol for semantic findings.
- Two-reviewer agreement sample with percent agreement and Cohen's kappa when
  enough labels exist.
- Wilson intervals for simple rates.
- Bootstrap confidence intervals over skill-task-contract triples.
- Utility metrics beside security metrics.

Acceptance gate:

- Tables distinguish realized violations, attempted overreach, drift
  disagreement, missing outputs, oracle failures, benign task success, and
  canary movement.

## P6: Mitigations And Runtime Report Cards

Goal: show what improves security conformance, not only what fails.

Milestone outputs:

- Runtime security report card format.
- RP6 hardened profile results.
- Least-privilege baseline or SkillScope-style policy comparison where
  feasible.
- Guardrail baseline for approval/tool/network/persistence controls where
  feasible.
- Ablations for filesystem scope, write scope, network egress, approval policy,
  tool exposure, and persistence.

Acceptance gate:

- The paper can quantify drift reduction and utility cost for at least one
  mitigation family.

## P7: Submission And Artifact Package

Goal: make the paper and artifact acceptable to top-tier review.

Milestone outputs:

- Full paper draft with figures, tables, threat model, ethics, and limitations.
- Artifact README with clean-checkout reproduction.
- `SECURITY.md`, `CITATION.cff`, license, and data card.
- Anonymous artifact package for double-blind venues.
- Safe release policy for synthetic canaries and adversarial skills.
- AI-use disclosure text for venues that require it.

Acceptance gate:

- A reviewer can reproduce the main tables from a clean checkout and understand
  exactly which claims are supported by which traces.

## Priority Order

1. P0 evidence integrity.
2. P1 claim contract.
3. P2 instrumentation expansion.
4. P3 runtime expansion.
5. P4 benchmark expansion.
6. P5 statistics and adjudication.
7. P6 mitigations.
8. P7 submission package.

Do not scale the benchmark before P0 is complete. Scaling weak evidence creates
more cleanup work and reduces confidence.

## Submission Targets

| Target | Recommended Use |
| --- | --- |
| Workshop / technical report | After P0-P2, to get feedback on method and artifact shape. |
| NDSS 2027 Fall | Only if P0-P5 are substantially complete by late July 2026. |
| IEEE S&P 2027 second cycle | Good target if P0-P6 mature by October 2026. |
| USENIX Security 2027 Cycle 2 | Best target for a mature systems-security measurement artifact by January 2027. |

## Go / No-Go Gates

| Gate | Go Condition | No-Go Signal |
| --- | --- | --- |
| Workshop | Current MVP reruns cleanly and new instrumentation has at least one case | Path leaks, unverifiable provenance, or unclear claims. |
| Short paper | 10 skills, 30 triples, 3 profiles, repeat policy, clean artifact | Only RP2/RP3 or only controlled Python fixtures. |
| Full top-tier paper | 40 skills, 120+ runs, 4+ profiles or explicit narrowed scope, adjudication, baselines, artifact package | Missing approval/tool/persistence evidence, no repeats, no mitigation baseline. |
