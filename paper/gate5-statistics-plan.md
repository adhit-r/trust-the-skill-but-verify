# Gate 5 Statistics Plan

Status: plan and scaffold only. No Gate 5 full-paper statistics, confidence
intervals, bootstrap intervals, hypothesis tests, reviewer agreement measures,
or adjudicated aggregate results have been computed here.

## Scope

Gate 5 prepares the evaluation layer needed before the paper can make
quantitative claims beyond the current bounded feasibility and deterministic
fixture-stability evidence. This plan defines the units, inputs, estimands,
analysis methods, and evidence gates for future statistics.

## Inputs

Required machine-readable inputs before analysis:

- Validated run manifests with `skill_id`, `task_id`, `contract_id`,
  `variant_id`, `repeat_id`, runtime profile, prompt hash, workspace snapshot
  hash, and contract hash.
- Validated trace files and contract findings.
- Expected-output metadata for task-success and missing-output judgments.
- The paired-runtime summary denominator layer in
  `results/derived/paired-runtime-summary.json`.
- A frozen inclusion/exclusion table for promoted paper cases.
- Completed manual adjudication exports using
  `paper/gate5-adjudication-form.md` or a field-equivalent CSV/JSONL form.
- A versioned analysis script or notebook that reads only validated artifacts.

## Units

| Unit | Definition | Primary Use |
| --- | --- | --- |
| Run | One execution of one skill-task-contract-variant-repeat under one runtime profile | Trace validity and per-runtime findings |
| Runtime pair | Two matched runs with fixed skill, task, contract, variant, repeat, prompt hash, and workspace hash | Drift and paired disagreement |
| Skill-task-contract triple | One skill, task, and contract combination, optionally with benign and adversarial variants | Bootstrap resampling unit |
| Case family | Related triples grouped by workload and risk surface | Category-level reporting |
| Review item | One semantic finding or run-pair candidate sent to manual review | Adjudication and agreement |

## Primary Estimands

- Realized contract violation rate.
- Attempted overreach rate.
- Runtime-pair disagreement rate.
- Benign task success rate.
- Missing expected output rate.
- Canary observation rate by allowed and denied sink.
- Oracle failure and instrumentation artifact rates.

## Planned Methods

- Report raw numerators and denominators for every rate.
- Use Wilson intervals for simple binomial proportions only after the
  numerator, denominator, and inclusion rules are frozen.
- Use bootstrap intervals over skill-task-contract triples for category-level
  and runtime-pair comparisons once the promoted benchmark has enough triples.
- Use hierarchical bootstrap by skill when multiple tasks or variants come from
  the same skill.
- Use paired disagreement counts for runtime-pair analysis.
- Consider McNemar-style paired analysis only after enough matched runtime-pair
  observations exist for the target comparison.
- Report percent agreement and Cohen's kappa only after two independent
  reviewers classify the same frozen sample. If class counts are too sparse,
  report the limitation instead of forcing kappa.

## Nonclaims

This scaffold does not support:

- prevalence claims,
- completed confidence intervals,
- completed bootstrap intervals,
- completed hypothesis tests,
- completed reviewer agreement,
- defense-success claims,
- model-mediated repeat-stability claims,
- product-scale RP6 causality claims.

## Planned Output Schema

Future statistics outputs should be written to a new result artifact only after
the evidence gates below pass. A minimal JSON shape is:

```json
{
  "schema_version": "0.1",
  "status": "computed_from_validated_gate5_inputs",
  "analysis_script": "tools/<future-statistics-tool>.py",
  "input_manifest_refs": [],
  "review_export_refs": [],
  "frozen_inclusion_table_ref": "",
  "rates": [],
  "intervals": [],
  "paired_comparisons": [],
  "reviewer_agreement": [],
  "exclusions": [],
  "claim_boundaries": []
}
```

Do not populate this schema with placeholder numerical results.

## Current Denominator Artifact

`results/derived/paired-runtime-summary.json` groups existing comparison
artifacts by skill, task, contract, variant, and repeat. It provides a
machine-readable denominator layer for later paired-runtime statistics, but it
does not compute Wilson intervals, bootstrap intervals, McNemar-style tests,
manual-review agreement, or prevalence estimates.

## Current Descriptive-Rate Artifact

`benchmark/manifests/gate5-paper-inclusion.json` freezes the current 60-case
inclusion table for descriptive-rate accounting. `results/derived/gate5-descriptive-rates.json`
reports 22 raw inventory and coverage rate records from that table. These
artifacts do not compute confidence intervals, bootstrap intervals,
McNemar-style tests, manual-review agreement, or prevalence estimates.

`benchmark/review/gate5-review-queue.json` adds a deterministic queue over the
same 60-case denominator. It records 50 paired-summary mapped items, 10
metadata-only unmapped items, and 50 first-pass blinding-eligible items. It is
not a completed review export and does not contain reviewer IDs, adjudication,
reviewer agreement, confidence intervals, hypothesis tests, prevalence
estimates, or paper-grade completion evidence.

`benchmark/review/gate5-review-packet-index.json` expands that queue into a
packet-index layer with exact comparison, run/finding-file, trace, hash, and
pair-pointer refs. The current index has 60 packet records, 50 indexed
comparison refs, 100 trace refs, and 10 metadata-only blocked packets. It is
not a blinded packet export and does not contain raw trace content, completed
reviews, reviewer IDs, agreement metrics, adjudication records, or statistical
results.

`benchmark/review/gate5-blinded-packet-bundle.json` derives a first-pass
blinded export layer from the packet index. It exports 50 runtime-label-blinded
pair-review packets using opaque evidence identifiers and runtime slots, while
leaving 10 unmapped cases blocked as metadata-only records. It is still
pre-review and pre-statistics: no completed reviews, reviewer agreement,
adjudication, intervals, hypothesis tests, prevalence estimates, or paper-grade
completion claims are made.

`benchmark/review/gate5-review-export-templates.json` creates two blank
first-pass human-review templates over the same 50 blinded pair-review units.
The templates are not completed human reviews, do not claim human reviewer
identities, and do not support reviewer agreement, adjudication, statistics,
prevalence estimates, or paper-grade completion claims. Future completed
exports must validate separately with `tools/validate_gate5_completed_review_export.py`.

## Evidence Gates

Gate 5 remains open until all of the following are true:

- Paper case inclusion/exclusion decisions are frozen and reviewable.
- Every counted run has a validating trace and findings artifact.
- Every semantic finding in the sampled set has at least two independent
  reviews or is explicitly excluded from agreement analysis.
- Adjudication records exist for reviewer disagreements.
- Denominators are linked to manifests rather than hand-entered prose.
- Analysis scripts are deterministic and rerunnable from a clean checkout.
- Generated statistics are linked back to the claim ledger only after the
  above gates pass.
