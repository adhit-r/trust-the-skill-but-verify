# Gate 5 Descriptive Rates

Raw descriptive denominator and rate artifact built from the frozen Gate 5 inclusion table; not completed statistics, not confidence intervals, not hypothesis tests, not reviewer agreement, not prevalence, not source-mix evidence completion, and not paper-grade completion evidence.

## Aggregate

- Frozen cases: `132`
- Included cases: `132`
- Excluded cases: `0`
- Unique skills: `44`
- Source-mix skills: `first_party=9`, `public=17`, `synthetic=18`
- Source-mix cases: `first_party=27`, `public=51`, `synthetic=54`
- Cases with paired-summary group: `122`
- Cases without paired-summary group: `10`
- Included pair count: `122`

This artifact reports raw descriptive rates only. It does not report Wilson intervals, bootstrap intervals, McNemar tests, reviewer agreement, or prevalence.

## Rates

| Metric | Slice | Numerator | Denominator | Value |
| --- | --- | ---: | ---: | ---: |
| `included_case_share` | `all=all` | 132 | 132 | 1.000000 |
| `paired_summary_mapped_case_share` | `all=all` | 122 | 132 | 0.924242 |
| `source_mix_case_share` | `source_mix_label=first_party` | 27 | 132 | 0.204545 |
| `source_mix_skill_share` | `source_mix_label=first_party` | 9 | 44 | 0.204545 |
| `source_mix_case_share` | `source_mix_label=public` | 51 | 132 | 0.386364 |
| `source_mix_skill_share` | `source_mix_label=public` | 17 | 44 | 0.386364 |
| `source_mix_case_share` | `source_mix_label=synthetic` | 54 | 132 | 0.409091 |
| `source_mix_skill_share` | `source_mix_label=synthetic` | 18 | 44 | 0.409091 |
| `category_case_share` | `category=API workflow` | 18 | 132 | 0.136364 |
| `category_case_share` | `category=MCP/tool workflow` | 18 | 132 | 0.136364 |
| `category_case_share` | `category=compliance/audit` | 15 | 132 | 0.113636 |
| `category_case_share` | `category=data extraction` | 21 | 132 | 0.159091 |
| `category_case_share` | `category=document automation` | 21 | 132 | 0.159091 |
| `category_case_share` | `category=local file operations` | 18 | 132 | 0.136364 |
| `category_case_share` | `category=repository maintenance` | 21 | 132 | 0.159091 |
| `case_status_share` | `case_status=current_mvp` | 2 | 132 | 0.015152 |
| `case_status_share` | `case_status=current_pilot` | 130 | 132 | 0.984848 |
| `evidence_stage_share` | `evidence_stage=mvp` | 2 | 132 | 0.015152 |
| `evidence_stage_share` | `evidence_stage=pilot` | 130 | 132 | 0.984848 |
| `runtime_profile_case_coverage_share` | `runtime_profile=RP2` | 129 | 132 | 0.977273 |
| `runtime_profile_case_coverage_share` | `runtime_profile=RP3` | 129 | 132 | 0.977273 |
| `runtime_profile_case_coverage_share` | `runtime_profile=RP5` | 3 | 132 | 0.022727 |

## Next Dependencies

- Use the existing manual review queue and add completed two-reviewer records before reviewer agreement claims.
- Promote first-party/public source-provenance entries into executable evidence before claiming source-mix evidence completion.
- Add repeat-backed analysis before Wilson, bootstrap, McNemar, or other statistical claims.
- Treat 40/120 as a manifest/source-provenance floor only until repeat, statistics, and adjudication evidence catch up.
