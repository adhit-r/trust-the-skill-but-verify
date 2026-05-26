# Gate 5 Review Export Templates

Gate 5 blank first-pass human-review export templates over the blinded packet bundle; these templates are not completed reviews and include no human reviewer identity, agreement metric, adjudication record, completed statistic, prevalence estimate, or paper-grade completion evidence.

## Aggregate

- Templates: `2`
- Assigned packets per template: `50`
- Assigned pair-review units per template: `50`
- Blocked metadata-only packets: `10`
- Completed review exports: `0`
- Human reviewer identities claimed: `0`
- Agreement metrics: `0`
- Adjudication records: `0`

This artifact is a review-template package only. It contains no completed human reviews, reviewer identities, reviewer agreement, adjudication records, statistics, prevalence estimates, or paper-grade completion claims.

## Templates

| Export | Reviewer slot | Status | Items | Counts as human review |
| --- | --- | --- | ---: | --- |
| `gate5-reviewer_a-first-pass-template` | `reviewer_a` | `not_started` | 50 | `False` |
| `gate5-reviewer_b-first-pass-template` | `reviewer_b` | `not_started` | 50 | `False` |

## Blocked Packets

`10` packets remain metadata-only and are not assigned to the first-pass review templates.

## Next Dependencies

- Copy one template per real independent human reviewer and fill every response before using it as completed review evidence.
- Do not count Codex-assisted or synthetic reviewer outputs as human review evidence.
- Run the completed-review validator before computing agreement or adjudication artifacts.
- Compute agreement and adjudication in separate artifacts after two completed human exports cover the same frozen item set.
