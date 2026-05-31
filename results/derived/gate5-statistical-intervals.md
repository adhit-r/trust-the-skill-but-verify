# Gate 5 Statistical Intervals

Non-human Wilson and bootstrap interval artifact over the curated Gate 5 denominator and existing paired-runtime summary. It is not an ecosystem prevalence estimate, not a completed human/manual review, not reviewer agreement, not adjudication, not a McNemar hypothesis-test result, not source-mix evidence completion, not commercial-runtime behavior, not defense-success evidence, and not paper-grade completion by itself. Human review remains 0% until real reviewers complete the review exports.

## Aggregate

- Frozen cases: `132`
- Included cases: `132`
- Unique skills: `44`
- Paired-summary mapped cases: `122`
- Paired-summary unmapped cases: `10`
- Paired-runtime pair records: `214`
- Wilson intervals: `36`
- Case bootstrap intervals: `18`
- Hierarchical bootstrap intervals: `6`
- McNemar results: `0`
- Completed human reviews: `0`

## Paired Runtime Summary

- Majority pair classification: `no_pairwise_disagreement`
- Median pair disagreement count: `0.000000`
- Positive disagreement pairs: `62`
- Pairwise disagreement finding count: `232`
- Max pair severity: `critical`

Max severity is computed from comparator finding-set deltas only; it is reported beside majority/median behavior and is not human-adjudicated severity.

## Wilson Intervals

| Metric | Slice | Numerator | Denominator | Estimate | 95% Lower | 95% Upper |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `included_case_share` | `all=all` | 132 | 132 | 1.000000 | 0.971721 | 1.000000 |
| `paired_summary_mapped_case_share` | `all=all` | 122 | 132 | 0.924242 | 0.866159 | 0.958332 |
| `source_mix_case_share` | `source_mix_label=first_party` | 27 | 132 | 0.204545 | 0.144556 | 0.281245 |
| `source_mix_skill_share` | `source_mix_label=first_party` | 9 | 44 | 0.204545 | 0.111533 | 0.345006 |
| `source_mix_case_share` | `source_mix_label=public` | 51 | 132 | 0.386364 | 0.307633 | 0.471522 |
| `source_mix_skill_share` | `source_mix_label=public` | 17 | 44 | 0.386364 | 0.257212 | 0.533764 |
| `source_mix_case_share` | `source_mix_label=synthetic` | 54 | 132 | 0.409091 | 0.328941 | 0.494382 |
| `source_mix_skill_share` | `source_mix_label=synthetic` | 18 | 44 | 0.409091 | 0.276879 | 0.555902 |
| `category_case_share` | `category=API workflow` | 18 | 132 | 0.136364 | 0.088028 | 0.205265 |
| `category_case_share` | `category=MCP/tool workflow` | 18 | 132 | 0.136364 | 0.088028 | 0.205265 |
| `category_case_share` | `category=compliance/audit` | 15 | 132 | 0.113636 | 0.070086 | 0.179039 |
| `category_case_share` | `category=data extraction` | 21 | 132 | 0.159091 | 0.106473 | 0.230990 |
| `category_case_share` | `category=document automation` | 21 | 132 | 0.159091 | 0.106473 | 0.230990 |
| `category_case_share` | `category=local file operations` | 18 | 132 | 0.136364 | 0.088028 | 0.205265 |
| `category_case_share` | `category=repository maintenance` | 21 | 132 | 0.159091 | 0.106473 | 0.230990 |
| `case_status_share` | `case_status=current_mvp` | 2 | 132 | 0.015152 | 0.004165 | 0.053560 |
| `case_status_share` | `case_status=current_pilot` | 130 | 132 | 0.984848 | 0.946440 | 0.995835 |
| `evidence_stage_share` | `evidence_stage=mvp` | 2 | 132 | 0.015152 | 0.004165 | 0.053560 |
| `evidence_stage_share` | `evidence_stage=pilot` | 130 | 132 | 0.984848 | 0.946440 | 0.995835 |
| `runtime_profile_case_coverage_share` | `runtime_profile=RP2` | 129 | 132 | 0.977273 | 0.935311 | 0.992241 |
| `runtime_profile_case_coverage_share` | `runtime_profile=RP3` | 129 | 132 | 0.977273 | 0.935311 | 0.992241 |
| `runtime_profile_case_coverage_share` | `runtime_profile=RP5` | 3 | 132 | 0.022727 | 0.007759 | 0.064689 |
| `pair_classification_share` | `classification=mitigation_report_card_comparison` | 28 | 214 | 0.130841 | 0.092099 | 0.182603 |
| `pair_classification_share` | `classification=no_pairwise_disagreement` | 143 | 214 | 0.668224 | 0.602661 | 0.727854 |
| `pair_classification_share` | `classification=profile_conditioned_semantic_fixture` | 28 | 214 | 0.130841 | 0.092099 | 0.182603 |
| `pair_classification_share` | `classification=runtime_drift_candidate` | 15 | 214 | 0.070093 | 0.042934 | 0.112415 |
| `runtime_pair_share` | `runtime_pair=RP2__RP1` | 12 | 214 | 0.056075 | 0.032365 | 0.095441 |
| `runtime_pair_share` | `runtime_pair=RP2__RP3` | 162 | 214 | 0.757009 | 0.695343 | 0.809611 |
| `runtime_pair_share` | `runtime_pair=RP2__RP6` | 14 | 214 | 0.065421 | 0.039366 | 0.106802 |
| `runtime_pair_share` | `runtime_pair=RP3__RP1` | 12 | 214 | 0.056075 | 0.032365 | 0.095441 |
| `runtime_pair_share` | `runtime_pair=RP3__RP6` | 14 | 214 | 0.065421 | 0.039366 | 0.106802 |
| `positive_pair_disagreement_share` | `all=all` | 62 | 214 | 0.289720 | 0.233074 | 0.353781 |
| `pair_max_severity_share` | `max_severity=none` | 152 | 214 | 0.710280 | 0.646219 | 0.766926 |
| `pair_max_severity_share` | `max_severity=low` | 11 | 214 | 0.051402 | 0.028941 | 0.089684 |
| `pair_max_severity_share` | `max_severity=high` | 11 | 214 | 0.051402 | 0.028941 | 0.089684 |
| `pair_max_severity_share` | `max_severity=critical` | 40 | 214 | 0.186916 | 0.140374 | 0.244499 |

## Bootstrap Intervals

| Method | Metric | Slice | Estimate | 95% Lower | 95% Upper |
| --- | --- | --- | ---: | ---: | ---: |
| `nonparametric_case_bootstrap` | `paired_summary_mapped_case_share` | `all=all` | 0.924242 | 0.871212 | 0.962121 |
| `nonparametric_case_bootstrap` | `source_mix_case_share` | `source_mix_label=first_party` | 0.204545 | 0.136364 | 0.272917 |
| `nonparametric_case_bootstrap` | `source_mix_case_share` | `source_mix_label=public` | 0.386364 | 0.310606 | 0.469697 |
| `nonparametric_case_bootstrap` | `source_mix_case_share` | `source_mix_label=synthetic` | 0.409091 | 0.325758 | 0.492424 |
| `nonparametric_case_bootstrap` | `category_case_share` | `category=API workflow` | 0.136364 | 0.083333 | 0.196970 |
| `nonparametric_case_bootstrap` | `category_case_share` | `category=MCP/tool workflow` | 0.136364 | 0.083333 | 0.196970 |
| `nonparametric_case_bootstrap` | `category_case_share` | `category=compliance/audit` | 0.113636 | 0.068182 | 0.174242 |
| `nonparametric_case_bootstrap` | `category_case_share` | `category=data extraction` | 0.159091 | 0.106061 | 0.227273 |
| `nonparametric_case_bootstrap` | `category_case_share` | `category=document automation` | 0.159091 | 0.098485 | 0.219697 |
| `nonparametric_case_bootstrap` | `category_case_share` | `category=local file operations` | 0.136364 | 0.083333 | 0.196970 |
| `nonparametric_case_bootstrap` | `category_case_share` | `category=repository maintenance` | 0.159091 | 0.098485 | 0.219697 |
| `nonparametric_case_bootstrap` | `case_status_share` | `case_status=current_mvp` | 0.015152 | 0.000000 | 0.037879 |
| `nonparametric_case_bootstrap` | `case_status_share` | `case_status=current_pilot` | 0.984848 | 0.962121 | 1.000000 |
| `nonparametric_case_bootstrap` | `evidence_stage_share` | `evidence_stage=mvp` | 0.015152 | 0.000000 | 0.037879 |
| `nonparametric_case_bootstrap` | `evidence_stage_share` | `evidence_stage=pilot` | 0.984848 | 0.962121 | 1.000000 |
| `nonparametric_case_bootstrap` | `runtime_profile_case_coverage_share` | `runtime_profile=RP2` | 0.977273 | 0.946970 | 1.000000 |
| `nonparametric_case_bootstrap` | `runtime_profile_case_coverage_share` | `runtime_profile=RP3` | 0.977273 | 0.946970 | 1.000000 |
| `nonparametric_case_bootstrap` | `runtime_profile_case_coverage_share` | `runtime_profile=RP5` | 0.022727 | 0.000000 | 0.053030 |
| `hierarchical_skill_case_bootstrap` | `paired_summary_mapped_case_share` | `all=all` | 0.924242 | 0.848485 | 0.977273 |
| `hierarchical_skill_case_bootstrap` | `source_mix_case_share` | `source_mix_label=first_party` | 0.204545 | 0.090909 | 0.340909 |
| `hierarchical_skill_case_bootstrap` | `source_mix_case_share` | `source_mix_label=public` | 0.386364 | 0.250000 | 0.522727 |
| `hierarchical_skill_case_bootstrap` | `source_mix_case_share` | `source_mix_label=synthetic` | 0.409091 | 0.272727 | 0.545455 |
| `hierarchical_skill_case_bootstrap` | `evidence_stage_share` | `evidence_stage=mvp` | 0.015152 | 0.000000 | 0.045455 |
| `hierarchical_skill_case_bootstrap` | `evidence_stage_share` | `evidence_stage=pilot` | 0.984848 | 0.954545 | 1.000000 |

## Deferred Analyses

- McNemar-style analysis: `deferred_not_reported`
- Human/manual review: `0.0%` complete

Current paired-runtime records are comparator classifications and finding-set deltas, not a frozen binary human-adjudicated matched outcome table. A McNemar-style result would overstate the evidence at this stage.

## Next Dependencies

- Complete real two-reviewer human review exports before reviewer agreement or Cohen's kappa claims.
- Add binary matched outcome labels before McNemar-style hypothesis-test reporting.
- Keep all intervals scoped to the curated Gate 5 denominator rather than ecosystem prevalence.
- Promote more source-provenance entries into executable evidence before claiming source-mix evidence completion.
