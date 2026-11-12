# Runtime Report-Card Summary

This table is generated from `results/derived/runtime-report-cards/*_report_card.json`.
It is paper-facing source material only for the evidence levels named below.
It does not claim commercial-runtime behavior, public-network behavior, defense success, source-mix completion, prevalence, or completed human review.

| Runtime | Paper role | Runs | Trace-valid | Realized violation runs | Attempted-overreach runs | Missing-output runs | Benign task success | Comparison coverage | Boundary |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `RP1` | Restricted-hosted simulator | 12 | 12 | 0 | 2 | 12 | 0/6 (0.000) | 24/36 (0.667) | Simulator-backed only; not hosted-provider behavior. |
| `RP2` | Local controlled fixture | 136 | 136 | 13 | 0 | 0 | 7/7 (1.000) | 236/236 (1.000) | Controlled local adapter evidence; not commercial local-agent behavior. |
| `RP3` | Docker-backed controlled fixture | 136 | 136 | 12 | 6 | 3 | 7/7 (1.000) | 236/236 (1.000) | Container-backed supported-trace evidence; not syscall-complete tracing. |
| `RP5` | Plugin-style fixture | 3 | 3 | 0 | 1 | 0 | 2/2 (1.000) | NA | Fixture-backed plugin lifecycle evidence; not commercial plugin-store or live host API behavior. |
| `RP6` | Policy-hardened report card | 89 | 89 | 0 | 8 | 5 | 7/7 (1.000) | 176/188 (0.936) | Mitigation/report-card pilot with utility cost reported; not defense success. |

## Reading Notes

- Realized violation runs and attempted-overreach runs are separate; blocked or failed denied actions are not counted as realized violations.
- `Benign task success` is computed over report-card rows labeled benign; rows with unknown role remain in aggregate run counts but not in that rate.
- `Comparison coverage` is unsupported for profiles with no pairwise comparison denominator, such as the current RP5 fixture.
- RP6 rows are mitigation/report-card evidence and must be reported with missing-output and utility-cost context.

## Source Artifacts

- `RP1`: `results/derived/runtime-report-cards/rp1_report_card.json`
- `RP2`: `results/derived/runtime-report-cards/rp2_report_card.json`
- `RP3`: `results/derived/runtime-report-cards/rp3_report_card.json`
- `RP5`: `results/derived/runtime-report-cards/rp5_report_card.json`
- `RP6`: `results/derived/runtime-report-cards/rp6_report_card.json`
