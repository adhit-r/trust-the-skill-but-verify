# Top-Tier Research Review

Review date: 2026-05-23

Project reviewed: `Trust the Skill, Verify the Runtime: Differential Security Testing for Portable AI Agent Skills`

## Executive Verdict

The project has a strong research core and a credible path to a high-impact
security paper, but it is not yet ready for a top-tier systems-security
submission. The current state is best described as a well-instrumented pilot
artifact with four case families, RP2/RP3 execution, contract checking, and
paper-safe evidence boundaries.

The strongest contribution is the framing: treat the runtime as the experimental
variable and measure whether identical skill-task-contract triples preserve
security behavior across host profiles. That is a cleaner and more defensible
angle than another skill scanner, malicious-skill corpus, or prompt-injection
benchmark.

The main blocker is evidence depth. The current results show feasibility and
motivating drift, but they do not yet support prevalence claims, broad runtime
claims, approval/tool/persistence claims, or full product behavior claims.

Acceptability if submitted today:

| Venue Tier | Verdict | Reason |
| --- | --- | --- |
| Top-4 security conference | No-go | Scale, runtime coverage, instrumentation coverage, and statistical treatment are still pilot-level. |
| Strong workshop / artifact track | Plausible | The contract-trace-profile method and controlled fixtures are coherent and reproducible enough for feedback. |
| Full paper after roadmap completion | Plausible | If expanded to 40+ skills, 3+ runtimes, repeated runs, tool/approval/persistence instrumentation, and baselines. |

## Current Project Status

At review time, the repository was clean and synchronized with `origin/main` at
the paper-spine commit range ending in:

```text
24cf76b Add top-tier research review roadmap
```

Implemented project layers:

| Layer | Current State | Review Judgment |
| --- | --- | --- |
| Framing | `RESEARCH_ROADMAP.md`, `DRIFT_TAXONOMY_METRICS.md`, `SECURITY_CONTRACT_MODEL.md`, `RELATED_WORK.md` | Strong conceptual base; needs sharper differentiation against May 2026 skill-security papers. |
| Runtime profiles | RP1-RP6 YAML profiles exist; RP2/RP3 are executable in current evidence | Good profile abstraction; most profiles are not yet evaluated. |
| Adapters | RP2 local execution and RP3 Docker sandbox live paths exist | Good pilot; names still imply dry-run in some classes despite live behavior. |
| Trace model | Normalized JSONL events, profile hashes, run identity, instrumentation status, canary scanning | Good base; activation, approval, tool, connector, and persistence events are mostly future-facing. |
| Contract model | YAML contracts, schema validation, event matching, canary and output-oracle findings | Good MVP base; comparator now enforces pair comparability for current RP2/RP3 artifacts. |
| Experiments | Repo-audit, network-egress, AuditLens, docs-forge MVP runners and reproduction scripts | Strong for pilot; not enough for top-tier quantitative claims. |
| Paper artifacts | Method boundaries, case studies, tables, protocol, intro skeleton | Honest and reviewer-safe; this honesty should be preserved. |

## Evidence Snapshot

Current paper-facing evidence:

| Evidence Area | Current Value |
| --- | ---: |
| Case families | 4 |
| Paper-facing canonical traces | 24 |
| Tracked traces including older smoke | 30 |
| Recorded runtime-drift claims | 5 |
| Recorded pairwise disagreements | 24 |
| First-party seed case families | 2 |
| Controlled synthetic case families | 2 |

Case-family status:

| Case Family | What It Supports | Boundary |
| --- | --- | --- |
| Repo-audit | RP2 realizes `.env` read/report leak while RP3 fails closed | Synthetic npm-style fixture only. |
| Network-egress | Fake-sink send versus RP3 blocked egress without public internet contact | Controlled Python `urllib` and fake-sink path, not packet capture. |
| AuditLens P3/P4 | Sanitized compliance evidence and dashboard canary-flow behavior | Synthetic Acme fixture, not full AuditLens product or live connectors. |
| docs-forge P1/P2 | First-party docs workflow fixture with canary leak and source mutation probes | Controlled Python docs-forge-style fixture, not Node installer execution. |

The evidence is internally coherent. It is not yet externally broad.

## Codebase Assessment

The implementation has a clear architecture:

- `src/skilldiff/adapters/base.py` defines the shared run lifecycle, artifact
  layout, profile hashes, and run identity.
- `src/skilldiff/adapters/local.py` implements RP2 local execution over copied
  workspaces with wrapper-level read and network provenance.
- `src/skilldiff/adapters/docker.py` implements RP3 Docker execution, read-only
  source mounts, writable output mounts, network denial, and container-strace
  evidence for supported file-open syscalls.
- `src/skilldiff/traces/events.py` defines normalized event construction and
  validation.
- `src/skilldiff/contracts/checker.py` maps trace events to contract findings,
  canary findings, output-oracle findings, and attempted-versus-realized
  outcomes.
- `src/skilldiff/metrics/contract_compare.py` computes pairwise disagreement
  and drift-candidate reports from contract-check outputs.
- `tools/run_*_mvp.py` scripts make the pilot reproducible and regression-like.

Strengths:

- The run abstraction is credible: skill, task, contract, runtime profile,
  repeat, workspace seed, and artifact paths are tracked.
- The contract checker correctly separates realized violations from blocked or
  failed attempted overreach.
- The project keeps method boundaries explicit instead of overstating results.
- RP3's read-only mount and network-denial paths are useful concrete controls.
- The current paper artifacts already anticipate likely reviewer objections.

Technical weaknesses:

- `compare_contract_runs` now machine-checks the MVP comparability fields
  needed for RP2/RP3 drift candidates, but this guard must stay enforced as new
  runtimes, repeats, and model-mediated variants are added.
- Artifact-root-aware evidence resolution is now present, but new trace fields
  must preserve scrubbed placeholder semantics and clean-checkout rechecks.
- Current validation is script-based; there is no top-level CI matrix or
  conventional test suite.
- Runners encode expected summaries, which is useful for regression but can
  hide whether the expected metrics are conceptually complete.
- First-party pinned source hash lists are now verifier-enforced for
  docs-forge and AuditLens when source roots are supplied. The remaining gap is
  CI or clean-checkout access to those source roots, not missing hash lists.
- Trace vocabulary includes activation, approval, tool, and persistence
  concepts, but current adapters do not yet cover them enough for claims.

## Novelty Assessment

The core novelty remains defensible if the paper is positioned narrowly:

> Differential runtime security testing for portable agent skills, where the
> skill, task, workspace, and task-conditioned security contract are held fixed,
> and the runtime profile is varied to measure security conformance drift.

This is distinct from the closest 2026 work:

| Work | What It Does | Why This Project Is Different |
| --- | --- | --- |
| [Agent Skills in the Wild](https://arxiv.org/abs/2601.10338) | Large-scale skill vulnerability measurement and taxonomy. | This project measures execution-time runtime drift, not static vulnerability prevalence. |
| [SkillScope](https://arxiv.org/abs/2605.05868) | Task-conditioned least-privilege detection and constraining. | Least privilege is a mitigation/baseline here; the primary variable is runtime profile disagreement. |
| [Under the Hood of SKILL.md](https://arxiv.org/abs/2605.11418) | Registry discovery, selection, and governance attacks through skill text. | This project starts after selection: what happens when the selected skill executes under different runtimes. |
| [SkCC](https://arxiv.org/abs/2605.03353) | Cross-framework skill compilation and static security optimization. | Compilation is upstream; this project tests whether deployed runtimes preserve security semantics. |
| [SkillSafetyBench](https://arxiv.org/abs/2605.12015) | Runnable benchmark for skill-mediated safety failures. | This project needs to emphasize differential runtime conformance, not merely skill-facing attack success. |

The novelty risk is that reviewers may say: "This is just another agent-skill
safety benchmark." The paper should preempt that by making pairwise runtime
conformance the central unit of analysis, not attack success rate alone.

## Methodology Evaluation

Current methodology:

- Good for feasibility.
- Good for demonstrating trace/contract mechanics.
- Good for showing that RP2/RP3 can differ under controlled conditions.
- Not yet enough for prevalence, causal, or ecosystem-level conclusions.

What is missing for top-tier rigor:

| Gap | Why Reviewers Will Care | Required Fix |
| --- | --- | --- |
| Scale | Four case families is too small for general claims. | Expand to at least 40 skills and 120+ skill-task-contract runs for full paper. |
| Runtime diversity | RP2/RP3 only misses hosted, plugin, MCP, and hardened profiles. | Execute RP1/RP4/RP5/RP6 or clearly defer them. |
| Repeats | Single deterministic runs cannot handle agent nondeterminism. | Add 3 deterministic repeats and 5 model-mediated repeats where relevant. |
| Instrumentation coverage | D1/D3/tool/persistence are mostly not measured. | Add event emitters and profile support before claiming those classes. |
| Comparator invariants | The MVP now enforces skill/task/contract/prompt/workspace/variant/repeat equivalence, but expansion can regress this if new runners omit fields. | Keep no-unchecked-field validation in the claim ledger and CI for every new runtime profile. |
| External validity | Controlled Python fixtures may look artificial. | Add real execution slices and diverse skill categories. |
| Baselines | No comparison to least-privilege or runtime guardrails. | Add SkillScope-style policy baseline, hardened RP6, and possibly ClawGuard-like boundary checks. |
| Human review | Semantic findings need adjudication. | Add two-reviewer classification with agreement metrics. |
| Artifact evaluation | Security venues expect reproducibility. | Add CI, clean-checkout reproduction, anonymized artifact package, and release metadata. |

## Main Risks

| Risk | Severity | Mitigation |
| --- | --- | --- |
| Overclaiming current pilot as general evidence | Critical | Keep "pilot", "controlled fixture", and "feasibility" wording until scale gates pass. |
| Getting scooped by skill-safety benchmarks | High | Reframe hard around runtime conformance and differential testing. |
| Controlled fixtures look too synthetic | High | Add real first-party and third-party skills with full or partial real execution. |
| Instrumentation gaps create false negatives | High | Treat missing normalized events as instrumentation gaps, not security successes. |
| Public artifact leaks local paths or sensitive payloads | High | Integrate scrubber and safe-payload validation into reproduction. |
| Reviewer asks "why not just least privilege?" | Medium | Use least privilege as a mitigation baseline, not the research question. |
| Docker sandbox mistaken as a complete defense | Medium | Preserve boundary wording and add mitigation/utility metrics. |

## High-Impact Contributions To Target

The strongest full-paper contribution set should be:

1. A formal model of runtime-induced security drift for portable agent skills.
2. A task-conditioned security contract language for skill execution.
3. A normalized trace schema spanning file, process, network, activation,
   approval, tool, persistence, output, cleanup, and canary-flow events.
4. A differential execution harness that runs identical skill-task-contract
   triples across runtime profiles.
5. A benchmark spanning real and synthetic skills, benign and adversarial
   variants, multiple categories, and multiple runtimes.
6. A metric suite that separates realized violations, attempted overreach,
   runtime-pair disagreement, benign utility, missing output, and canary flow.
7. Mitigation report cards showing which runtime controls reduce drift while
   preserving task success.

The paper should not sell itself as a detector. It should sell itself as a
security conformance testing method for the agent-skill supply chain.

## Publication Strategy

Near-term best path:

| Target | Fit | Readiness |
| --- | --- | --- |
| Workshop at a top security venue | Early feedback on method and artifact | Good after evidence integrity fixes. |
| NDSS 2027 | Strong systems-security fit if the paper has real systems, artifacts, and AI/LLM security contribution | Fall 2026 cycle is more realistic than summer. |
| USENIX Security 2027 | Strong fit for reproducible systems-security measurement | Cycle 2 in January 2027 is realistic for full scale. |
| IEEE S&P 2027 | High bar; possible if the paper is very rigorous and artifact/anonymity are clean | November 2026 cycle is more realistic than June. |
| ACM CCS 2026 | The 2026 submission cycles are effectively too near or already passed for a full top-tier version from current state | Not primary unless aiming at artifact/demo/workshop side paths. |

Official venue context checked:

- [USENIX Security 2027](https://www.usenix.org/conference/usenixsecurity27) lists Cycle 1 submissions due August 25, 2026 and Cycle 2 due January 26, 2027.
- [IEEE S&P 2027](https://sp2027.ieee-security.org/cfpapers.html) lists June 11, 2026 and November 17, 2026 paper deadlines.
- [NDSS 2027](https://www.ndss-symposium.org/ndss2027/submissions/call-for-papers/) lists May 6, 2026 and August 19, 2026 submission deadlines, and explicitly includes security/privacy of AI and LLM systems in scope.
- [ACM CCS 2026](https://www.sigsac.org/ccs/CCS2026/call-for/call-for-papers.html) lists 2026 cycles and emphasizes artifact functionality/reproducibility and AI-use disclosure.

Recommended submission plan:

1. Aim for an early workshop or technical report after P0/P1/P2.
2. Aim for NDSS 2027 Fall only if P3/P4 complete by late July 2026.
3. Aim for IEEE S&P 2027 second deadline or USENIX Security 2027 Cycle 2 if the full benchmark and artifact package mature.

## Reviewer-Grade Acceptance Bar

Before a top-tier submission, the project should be able to answer these
questions with concrete evidence:

1. How many skill-task-contract triples were evaluated, and why are they
   representative?
2. What exact runtime profiles were executed, and which profile features explain
   observed drift?
3. How do we know two compared runs used the same skill, task, workspace,
   prompt, contract, and repeat?
4. How often did stricter runtimes block violations but break utility?
5. What happens when approval, MCP/tool access, persistence, and activation are
   included?
6. How stable are findings over repeats?
7. How many findings required manual adjudication, and what was reviewer
   agreement?
8. Which mitigations reduce realized violations without unacceptable missing
   outputs?
9. Can an external evaluator reproduce the key tables from a clean checkout?
10. Is the released artifact safe, anonymous, and free of real secrets/local
    leakage?

## Bottom Line

The direction is strong. The next phase should stop adding isolated pilots and
instead harden the measurement contract: integrity, comparability, coverage,
scale, statistics, and artifact packaging. If those gates are met, this can
become a serious systems-security measurement paper rather than a collection of
interesting skill-safety demos.
