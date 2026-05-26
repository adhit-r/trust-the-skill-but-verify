# Experiment Protocol

This protocol defines how the paper moves from the current baseline evidence
to a defensible top-tier full-paper evaluation. It is mapped to RM-11 and
should be updated before any new benchmark expansion changes the unit of
analysis.

## Study Goal

Measure whether portable agent skills preserve security behavior when the same
skill, task, and task-conditioned security contract are executed under different
runtime profiles.

The primary outcome is not "malicious skill detected." The primary outcome is
runtime conformance: whether observed behavior remains stable across runtimes
or changes into realized violations, attempted overreach, missing outputs,
approval changes, side effects, or canary movement.

## Unit of Analysis

| Unit | Definition | Used For |
| --- | --- | --- |
| Run | One execution of one skill-task-contract triple under one runtime profile and one repeat ID | Trace validity, contract checking |
| Runtime pair | Two runs with the same skill, task, contract, input workspace, and repeat ID but different runtime profiles | Pairwise drift and disagreement |
| Skill-task-contract triple | `(skill_id, task_id, contract_id)` with one benign and, where applicable, one adversarial variant | Primary statistical unit |
| Case family | Related triples grouped by skill and risk surface, such as docs-forge P1/P2 | Case-study and category analysis |
| Category | Document automation, repository maintenance, network egress, compliance audit, API workflow, MCP/tool workflow, local file operation | Aggregate reporting |

The current baseline slice contains five case families, twenty-eight canonical
trace files for the paper-facing cases, and 234 tracked raw trace files
including older smoke traces and expanded runtime fixtures. The full paper
should treat the current slice as feasibility evidence, not as prevalence
evidence.

## Research Questions To Measures

| RQ | Measurement | Primary Artifact | Figure/Table |
| --- | --- | --- | --- |
| RQ1: How often does behavior change across runtime profiles? | Runtime-pair disagreement rate; drift claim count; realized versus attempted outcomes | Contract comparison JSON and drift reports | F4, T5 |
| RQ2: Which runtime profiles and features are associated with risk? | Violation and attempted-overreach rates by filesystem, shell, network, approval, tool, persistence, and context features | Runtime profile matrix plus static scanner, reachability approximation, and ablations | F5, T1 |
| RQ3: Do activation metadata and SKILL.md instructions activate differently across hosts? | Expected activation, unexpected activation, non-activation, and host-specific routing differences | Activation trace events once D1 instrumentation is implemented | F1, T5 |
| RQ4: Can task-conditioned contracts predict unsafe behavior? | Contract violation rate, missing-output rate, oracle failure rate, false positive and false negative review | Contract findings and expected-output metadata | T6 |
| RQ5: Are approval prompts sufficient? | Approval-required action count, silent execution count, denial-respected count, prompt-target completeness | Approval trace events once D3 instrumentation is implemented | T6, T7 |
| RQ6: Which mitigations reduce drift while preserving utility? | Drift reduction, benign task success, missing-output increase, approval burden, component-disabled regressions | RP6 report card, static scanner baseline, Semia-style reachability approximation, action-boundary baseline, contract-derived least-privilege baseline, coarse mitigation ladder, minimal RP6 contrast matrix, and bounded RP6 component-ablation report card | F6, T7 |

Current baseline evidence directly supports RQ1 and RQ4 for RP2/RP3, partially
supports RQ2 for filesystem, network, tool-call, and persistence policy, and
partially supports RQ3/RQ5 only for controlled semantic-event representation.
RP1 adds promoted deterministic restricted-hosted simulator evidence for the
upload-oriented current subset, but it is not live hosted-provider evidence and
is excluded from RP2/RP3 drift aggregates. RP5 adds bounded local plugin-style
fixture evidence for install, activation, update metadata, bundled-resource
reads, scoped plugin storage, fixture host APIs, and activation negative
controls; it is not commercial plugin-store or live host API evidence. The
current package also includes an RP6 current-case mitigation report-card pilot,
a static scanner baseline, a Semia-style reachability approximation, an
action-boundary relevance baseline, a contract-derived least-privilege
baseline, a coarse mitigation ladder, and a minimal RP6 contrast matrix for
RQ6. It also includes a bounded component ablation report card over six RP6
controls and twelve generated ablation traces, but does not support Semia
equivalence, live guardrail efficacy, or defense-success claims.

## Runtime Profiles

The current executable comparison uses:

- RP2: local coding-agent profile with broad workspace access.
- RP3: Docker-sandboxed profile with explicit mounts, read-only source
  boundaries, and controlled network denial.

RP1 is available as a deterministic restricted-hosted simulator over a bounded
upload-oriented subset. It emits valid traces and report-card artifacts, but it
is not commercial hosted-runtime behavior, live provider instrumentation, live
MCP/plugin behavior, or public-network evidence.

RP5 is available as a bounded plugin-style fixture over local synthetic plugin
metadata, bundled resources, deterministic install/update behavior, fixture
host APIs, scoped plugin storage, and one activation negative control. It emits
valid traces and report-card artifacts, but it is not commercial plugin-store
behavior, live host API behavior, external MCP/server behavior, or
public-network evidence.

For a run pair to support a runtime-drift candidate, the comparator requires
matching `skill_id`, `task_id`, `contract_id`, `repeat_id`,
`workspace_snapshot_hash`, `task_prompt_hash`, and `variant_id`. The current
comparison artifacts report no unchecked comparator fields.

The full paper should add or promote RP4, RP5, RP6, and any live-hosted RP1
successor only when each profile has:

- a profile YAML file with a stable hash,
- an adapter or simulator that emits valid traces,
- at least one negative-control task,
- a clear statement of which security surfaces it can and cannot observe.

## Case Inclusion Criteria

A case may enter the paper evaluation only if all of the following hold:

- The skill source or synthetic fixture has a recorded provenance boundary.
- The task prompt is fixed and stored in the repository.
- The security contract validates against the schema.
- Expected functional outputs are specified.
- Synthetic secrets or canaries are labeled as synthetic and safe to publish.
- No public internet endpoint is required.
- The run emits a valid trace and contract findings file.
- The paper text can state whether the workload is full product execution,
  controlled fixture execution, or source-only provenance inspection.

Exclusion rules:

- Exclude cases with real credentials, customer data, live SaaS exports, or
  unsanitized local paths.
- Exclude cases where the runtime adapter fails before the skill can execute,
  unless the failure itself is the planned object of study.
- Exclude traces with incomplete run identity, missing terminal events, raw
  sensitive payload retention, or ambiguous canary provenance.

## Sample Size Targets

| Stage | Target | Claim Boundary |
| --- | --- | --- |
| Current baseline evidence | 5 case families, 28 paper-facing canonical traces, RP2/RP3 only | Feasibility and method evidence |
| Current controlled executable extension | 2 additional synthetic fixture families, 12 RP2/RP3 traces, and 6 comparison artifacts for data extraction and local file operations | Bounded fixture evidence only; no live SaaS/database/filesystem-sandbox, archive-tool, destructive-cleanup, prevalence, or runtime-drift finding claim |
| Current controlled fixture inventory | 20 skills and 60 skill-task-contract triples after promoting the planned inclusion entries; skill-origin source mix is 1 first-party, 1 public, and 18 synthetic skills | Controlled single-repeat RP2/RP3 fixture evidence only; source-mix gaps are computed but no source-mix completion, repeat stability, prevalence, live product, public-network, commercial-runtime, defense-success, or 40/120 completion claim |
| Current Gate 5 descriptive denominator | Frozen inclusion table over 60 current cases and 22 raw inventory/coverage rate records | Descriptive denominator and rate evidence only; no completed statistics, intervals, hypothesis tests, reviewer agreement, prevalence, source-mix completion, or paper-grade completion claim |
| Current planned-entry promotion | 44 formerly planned entries, 88 RP2/RP3 traces, and 44 comparison artifacts | Denominator and contract-check coverage only; generic-runner cases do not establish skill-specific product behavior or runtime-drift findings |
| Planned-inclusion deterministic repeat stability | 44 controlled planned-inclusion fixtures, repeat IDs 1-3, 264 RP2/RP3 observations, and 132 same-repeat RP2/RP3 pairs | Bounded deterministic fixture-stability evidence only; no completed statistics, reviewer agreement, prevalence, live product, public-network, commercial-runtime, or defense-success claim |
| Full-paper evidence floor | At least 40 skills and 120 skill-task-contract triples before repeats, across at least four runtime profiles or an equivalent-depth full-paper scope | Quantitative claims by category and runtime pair |
| Full benchmark stretch | 60 base skills, 60 adversarial variants, 3-5 tasks per skill, 4-6 runtime profiles | Strong systems-security benchmark contribution |

Do not make prevalence claims from the current baseline evidence. Use current
results to justify the method and select instrumentation priorities.

## Repeat-Run Plan

For deterministic controlled Python fixtures:

- Run each skill-task-profile at least once for current baseline evidence.
- Run each included full-paper fixture at least three times before deterministic
  stability reporting.
- Current RP6 strengthening evidence meets this deterministic threshold for the
  fourteen controlled RP6 current-case fixtures: repeat IDs 1, 2, and 3 produce
  42 trace-valid observations with matching outcome summaries. This remains a
  bounded fixture-stability result, not prevalence, statistical, or
  model-mediated stability evidence.
- Current planned-inclusion RP2/RP3 repeat-stability evidence meets this
  deterministic threshold for the 44 controlled planned-inclusion fixtures:
  repeat IDs 1, 2, and 3 produce 264 trace-valid observations and 132
  same-repeat RP2/RP3 pairs with matching outcome summaries. This remains
  bounded deterministic fixture-stability evidence and is not a completed
  statistical analysis or reviewer-adjudication result.

For model-mediated or nondeterministic agent runs:

- Run at least five repeats per skill-task-profile.
- Fix prompt text, workspace snapshot, contract hash, profile hash, model ID,
  model parameters, and tool policy where the runtime allows it.
- Report both per-repeat outcomes and per-triple aggregate outcomes.
- Never average away a realized security violation; if any repeat realizes a
  high-severity violation, report the maximum-severity outcome alongside the
  median or majority outcome.

## Nondeterministic Output Handling

Functional output checks should distinguish:

- task success,
- missing expected outputs,
- semantically acceptable variants,
- oracle failures,
- blocked unsafe behavior that prevents task completion,
- instrumentation failures.

The paper should not treat missing output as security success. A runtime that
blocks canary movement but fails the task is safer on data flow but worse on
utility.

## Manual Review Procedure

Manual review is required when:

- a new contract rule is introduced,
- a finding depends on semantic output interpretation,
- the trace lacks a normalized event for a visible adapter-level behavior,
- a benign run fails unexpectedly,
- a new case family is promoted from baseline evidence to paper evidence.

Reviewers should record:

- finding kind: realized violation, attempted overreach, runtime-pair
  disagreement, missing output, oracle failure, or instrumentation artifact,
- drift class: D1-D5,
- severity,
- evidence path,
- whether the finding is paper-claimable.

## Blinding And Agreement

For the full paper, at least two reviewers should independently classify a
sample of findings without runtime labels where possible. They may see event
types and targets but should not see whether the run came from RP2, RP3, or a
mitigation profile during the first pass.

Report agreement as percent agreement plus Cohen's kappa when there are enough
classified findings. Resolve disagreements by adjudication and keep the
adjudication notes in the artifact.

## Statistical Plan

Primary rates:

- realized contract violation rate,
- attempted overreach rate,
- runtime-pair disagreement rate,
- benign task success rate,
- missing expected output rate,
- canary observation rate.

Confidence intervals:

- Use Wilson intervals for simple binomial proportions.
- Use bootstrap confidence intervals over skill-task-contract triples for
  category-level and runtime-pair comparisons.
- Use hierarchical bootstrap by skill when multiple tasks come from the same
  skill.

Pairwise runtime comparisons:

- Report paired disagreement counts by runtime pair.
- Use McNemar-style paired analysis only after enough paired observations exist.
- Until then, present counts and confidence intervals without causal claims.

## Ablation Plan

Runtime-feature ablations:

- filesystem read scope: currently covered for RP6 fixture ablation,
- filesystem write scope: currently covered for RP6 fixture ablation,
- shell execution,
- network egress: currently covered for RP6 fixture ablation,
- approval requirement: currently covered for RP6 fixture ablation,
- tool or MCP availability: currently covered for RP6 semantic-tool fixture ablation,
- persistence or cache access: currently covered for RP6 file-backed persistence/cache fixture ablation,
- context inheritance.

Current artifact: `results/fixtures/rp6-policy-hardened/ablations/component_report_card.json`.
It disables one named RP6 fixture control at a time in generated profiles and
checks the resulting traces against the original contracts. It is not a
product-scale causal defense claim.

Skill-category ablations:

- document automation,
- repository maintenance,
- compliance audit,
- data extraction,
- API workflow,
- MCP/tool workflow,
- local file operation.

Attack-family ablations:

- canary leak,
- output-scope mutation,
- network canary leak,
- connector overreach,
- activation overreach,
- hidden persistence.

## Error Taxonomy

| Error Type | Meaning | Action |
| --- | --- | --- |
| Instrumentation gap | Behavior is visible in adapter logs but not normalized as a trace event | Do not count as metric until normalized; note as boundary evidence |
| Fixture mismatch | Workspace or fixture does not match the stated source boundary | Fix before paper use |
| Oracle gap | Expected output is underspecified or too brittle | Improve expected-output metadata |
| Benign utility failure | Benign run fails the task | Count separately from security success |
| Blocked-overreach confusion | Blocked unsafe action is counted as realized violation | Correct metrics and wording |
| Runtime failure | Adapter or container fails before skill execution | Exclude or mark as runtime failure |
| Path normalization leak | Trace preserves local machine paths | Scrub before safe publication |
| Nondeterministic trace | Same setup produces inconsistent findings | Add repeats and adjudication |

## Clean-Checkout Reproduction

The artifact should support this clean-checkout path:

```bash
python3 -m venv /tmp/skilldiff-venv
/tmp/skilldiff-venv/bin/pip install -r requirements-dev.txt
PYTHON_BIN=/tmp/skilldiff-venv/bin/python bash experiments/repo-audit-mvp/reproduce_repo_audit_mvp.sh
PYTHON_BIN=/tmp/skilldiff-venv/bin/python bash experiments/network-egress-mvp/reproduce_network_egress_mvp.sh
PYTHON_BIN=/tmp/skilldiff-venv/bin/python bash experiments/audit-lens-mvp/reproduce_audit_lens_mvp.sh
PYTHON_BIN=/tmp/skilldiff-venv/bin/python bash experiments/docs-forge-mvp/reproduce_docs_forge_mvp.sh
```

Docker must be available for RP3 reproduction. Public internet contact should
remain outside the benchmark boundary.

## Promotion Gates

A result can be promoted into the main paper only if:

- all relevant JSON/YAML artifacts validate,
- all cited trace files validate,
- no local machine paths remain in tracked artifacts,
- every numerical claim points to a manifest or drift report,
- the method-boundary text says what is not measured,
- the result is reproducible from a clean checkout or marked as a
  baseline-only observation.
