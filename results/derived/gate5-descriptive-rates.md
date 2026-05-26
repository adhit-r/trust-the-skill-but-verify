# Gate 5 Descriptive Rates

Raw descriptive denominator and rate artifact built from the frozen Gate 5 inclusion table; not completed statistics, not confidence intervals, not hypothesis tests, not reviewer agreement, not prevalence, not source-mix completion, and not paper-grade completion evidence.

## Aggregate

- Frozen cases: `60`
- Included cases: `60`
- Excluded cases: `0`
- Unique skills: `20`
- Source-mix skills: `first_party=1`, `public=1`, `synthetic=18`
- Source-mix cases: `first_party=3`, `public=3`, `synthetic=54`
- Cases with paired-summary group: `50`
- Cases without paired-summary group: `10`
- Included pair count: `50`

This artifact reports raw descriptive rates only. It does not report Wilson intervals, bootstrap intervals, McNemar tests, reviewer agreement, or prevalence.

## Rates

| Metric | Slice | Numerator | Denominator | Value |
| --- | --- | ---: | ---: | ---: |
| `included_case_share` | `all=all` | 60 | 60 | 1.000000 |
| `paired_summary_mapped_case_share` | `all=all` | 50 | 60 | 0.833333 |
| `source_mix_case_share` | `source_mix_label=first_party` | 3 | 60 | 0.050000 |
| `source_mix_skill_share` | `source_mix_label=first_party` | 1 | 20 | 0.050000 |
| `source_mix_case_share` | `source_mix_label=public` | 3 | 60 | 0.050000 |
| `source_mix_skill_share` | `source_mix_label=public` | 1 | 20 | 0.050000 |
| `source_mix_case_share` | `source_mix_label=synthetic` | 54 | 60 | 0.900000 |
| `source_mix_skill_share` | `source_mix_label=synthetic` | 18 | 20 | 0.900000 |
| `category_case_share` | `category=API workflow` | 9 | 60 | 0.150000 |
| `category_case_share` | `category=MCP/tool workflow` | 6 | 60 | 0.100000 |
| `category_case_share` | `category=compliance/audit` | 9 | 60 | 0.150000 |
| `category_case_share` | `category=data extraction` | 9 | 60 | 0.150000 |
| `category_case_share` | `category=document automation` | 9 | 60 | 0.150000 |
| `category_case_share` | `category=local file operations` | 6 | 60 | 0.100000 |
| `category_case_share` | `category=repository maintenance` | 12 | 60 | 0.200000 |
| `case_status_share` | `case_status=current_mvp` | 2 | 60 | 0.033333 |
| `case_status_share` | `case_status=current_pilot` | 58 | 60 | 0.966667 |
| `evidence_stage_share` | `evidence_stage=mvp` | 2 | 60 | 0.033333 |
| `evidence_stage_share` | `evidence_stage=pilot` | 58 | 60 | 0.966667 |
| `runtime_profile_case_coverage_share` | `runtime_profile=RP2` | 57 | 60 | 0.950000 |
| `runtime_profile_case_coverage_share` | `runtime_profile=RP3` | 57 | 60 | 0.950000 |
| `runtime_profile_case_coverage_share` | `runtime_profile=RP5` | 3 | 60 | 0.050000 |

## Next Dependencies

- Add manual review queue and completed two-reviewer records before reviewer agreement claims.
- Add public and additional first-party skills before claiming source-mix completion.
- Add repeat-backed analysis before Wilson, bootstrap, McNemar, or other statistical claims.
- Keep 40/120 full-paper completion blocked until the manifest reaches that floor.
