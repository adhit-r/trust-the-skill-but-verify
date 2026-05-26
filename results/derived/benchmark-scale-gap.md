# Benchmark Scale Gap

Current-to-target benchmark scale gap report. Current inventory entries are not proof that the mid-scale 20/60 or full-paper 40/120 floors are complete as paper-grade evidence; execution evidence remains bounded by runtime profiles, repeat coverage, adjudication, and source-mix labels.

provenance.source_mix.label is a skill-origin/source-mix accounting label; provenance.source_kind and provenance_level remain case-level evidence labels.

## Current Inventory

- Case entries: `60`
- Unique skills: `20`
- Unique skill-task-contract triples: `60`
- Declared case count: `60`
- Missing categories: ``
- Source-mix skill counts: `first_party=1`, `public=1`, `synthetic=18`

| Category | Current Skills | Current Triples | Mid-Scale Skill Target | Mid-Scale Skill Gap | Full-Paper Skill Target | Full-Paper Skill Gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| document automation | 3 | 9 | 3 | 0 | 6 | 3 |
| repository maintenance | 4 | 12 | 4 | 0 | 7 | 3 |
| compliance/audit | 3 | 9 | 3 | 0 | 5 | 2 |
| data extraction | 3 | 9 | 3 | 0 | 6 | 3 |
| API workflow | 3 | 9 | 3 | 0 | 6 | 3 |
| MCP/tool workflow | 2 | 6 | 2 | 0 | 5 | 3 |
| local file operations | 2 | 6 | 2 | 0 | 5 | 3 |

## Source Mix

| Source Mix | Current Skills | Current Cases | Mid-Scale Skill Target | Mid-Scale Skill Gap | Full-Paper Skill Target | Full-Paper Skill Gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| first_party | 1 | 3 | 5 | 4 | 9 | 8 |
| public | 1 | 3 | 8 | 7 | 17 | 16 |
| synthetic | 18 | 54 | 7 | 0 | 14 | 0 |

## Target Boundaries

- Mid-scale skill shortfall: `0`
- Mid-scale triple shortfall: `0`
- Full-paper skill shortfall: `20`
- Full-paper triple shortfall: `60`
- Mid-scale source-mix skill shortfall: `11`
- Full-paper source-mix skill shortfall: `24`
- Source-mix gaps are computed from explicit manifest labels, but source-mix completion is not claimed.
- This artifact does not claim benchmark prevalence, source-mix completion, repeat/statistical readiness, or 40/120 completion.

## Next Actions

- Add repeat coverage, source-mix evidence depth, and adjudication evidence before claiming paper-grade mid-scale completion.
- Add public and additional first-party skills before claiming source-mix target completion.
- Keep every promoted entry tied to tracked prompt, prompt hash, workspace snapshot hash, contract, expected output, canary policy, publication boundary, and safety status.
