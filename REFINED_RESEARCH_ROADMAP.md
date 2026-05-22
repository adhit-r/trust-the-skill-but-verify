# Refined Research Roadmap

This roadmap converts the current benchmark evidence into a top-tier full
systems-security paper. The only accepted end goal is a full-paper submission
suitable for NDSS, USENIX Security, IEEE S&P, or ACM CCS. Workshop, demo,
short-paper, and technical-report paths are out of scope for this roadmap.

All priorities below optimize for evidence integrity, runtime comparability,
instrumentation coverage, benchmark scale, statistical rigor, mitigation
baselines, and artifact readiness.

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

Top-tier full-paper readiness means the paper can defend all of the following:

- A clear formal model of runtime-induced security drift.
- A normalized trace and contract system that covers file, process, network,
  activation, approval, tool/MCP, persistence, output, cleanup, and canary-flow
  behavior.
- At least 40 skills and at least 120 skill-task-contract runs across at least
  four runtime profiles, or an explicitly justified equivalent-depth
  full-paper scope.
- Repeat-run evidence, uncertainty estimates, utility metrics, manual
  adjudication, and mitigation baselines.
- A clean, anonymous, reviewer-reproducible artifact package.

## P0: Evidence Integrity Gate

Goal: make the existing benchmark evidence reliable, rerunnable, and safe before
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

- A clean checkout can regenerate the current evidence tables without local path
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

- At least four profiles are executable for the full-paper target, with
  unsupported surfaces recorded in the adapter support matrix. If access limits
  force a narrower profile set, the paper must compensate with deeper
  instrumentation, repeats, and mitigation evidence rather than falling back to
  a weaker evidence claim.

## P4: Benchmark Expansion

Goal: turn current benchmark cases into a benchmark with enough breadth for quantitative
claims.

Full-paper dataset target:

- At least 40 skills.
- At least 120 skill-task-contract runs before repeats.
- At least four executable runtime profiles, with six profiles as the stretch
  target.
- Benign and adversarial variants for every included category.
- Categories: document automation, repository maintenance, compliance audit,
  network/API workflow, MCP/tool workflow, local file operation, and persistence.
- Clear separation of full-product execution, controlled fixture execution, and
  source-only inspection.

Acceptance gate:

- The paper can report category-level, runtime-pair-level, and
  mitigation-level metrics without relying on only the original benchmark
  families.

## P5: Experimental Rigor And Statistics

Goal: make the evaluation legible to systems-security reviewers.

Milestone outputs:

- Stable train/dev/test or benchmark/paper split for cases.
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

Goal: make the paper and artifact acceptable to top-tier full-paper review.

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

Only top-tier full-paper targets are in scope:

| Target | Readiness Requirement |
| --- | --- |
| NDSS 2027 Fall | P0-P5 complete, P2/P3 coverage defensible, benchmark scaled by late July 2026. |
| IEEE S&P 2027 second cycle | P0-P6 mature, threat model and statistics polished by October 2026. |
| USENIX Security 2027 Cycle 2 | Full benchmark, mitigation report cards, artifact package, and manuscript mature by January 2027. |
| ACM CCS next full cycle | Viable only with full top-tier evidence package and clear differentiation from skill-safety benchmarks. |

## Top-Tier Go / No-Go Gates

| Gate | Go Condition | No-Go Signal |
| --- | --- | --- |
| Concept | Runtime conformance drift is the central unit of analysis, not attack success alone. | Paper reads like another skill-safety benchmark. |
| Evidence integrity | Clean checkout reproduces main tables with provenance, claim-ledger, path-scrub, and comparator checks. | Any paper number lacks machine-checked evidence. |
| Instrumentation | File, process, network, activation, approval, tool/MCP, persistence, output, cleanup, and canary-flow surfaces are covered or explicitly bounded. | Missing observers are mistaken for security successes. |
| Runtime diversity | At least four runtime profiles are executable or an equivalent-depth full-paper scope is rigorously justified. | Results remain RP2/RP3-only without a strong causal or mitigation story. |
| Benchmark scale | At least 40 skills and 120+ skill-task-contract runs before repeats. | Claims rely on the original benchmark families. |
| Rigor | Repeats, utility metrics, uncertainty estimates, adjudication, and reviewer agreement are reported. | Single-run deterministic evidence is treated as general behavior. |
| Mitigations | RP6/report-card or least-privilege-style baselines quantify drift reduction and utility cost. | Paper only identifies failures and offers no actionable control comparison. |
| Artifact | Anonymous artifact package is safe, complete, documented, and reviewer-rerunnable. | Local paths, secrets, unclear licenses, or missing reproduction commands remain. |
