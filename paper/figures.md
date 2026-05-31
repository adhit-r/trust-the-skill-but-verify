# Paper Figures

This is the paper-facing figure index. Captions are intentionally bounded to
the current evidence state; do not remove simulator, fixture, report-card,
machine-only interval, or human-review boundaries when moving these into the
manuscript.

| Figure | Asset | Paper-Safe Caption | Must Not Imply |
| --- | --- | --- | --- |
| F1 Architecture | `paper/figures/fig1-architecture.svg` | SkillDiff holds skill, task, contract, workspace snapshot, task prompt, variant, and repeat identity fixed while varying runtime profile, then normalizes traces, checks contracts, compares runtime pairs, and emits bounded reports and claim-ledger evidence. | Runtime profile is fixed; RP1/RP4/RP5/RP6 are all equivalent current executable runtime-drift evidence. |
| F2 Trace lifecycle | `paper/figures/fig2-trace-lifecycle.svg` | A trace flows from fixed run metadata through raw observers, normalized `trace.jsonl` events, contract findings, runtime-pair comparison, and claim-ledger-backed reports. | Observer gaps are clean behavior; tracing is syscall-complete or packet-complete across all runtimes. |
| F3 Runtime profile matrix | `paper/figures/fig3-runtime-matrix.svg` | Runtime profiles are shown with evidence-level labels: RP2/RP3 current controlled executable evidence, RP1 simulator-backed contrast, RP4/RP5 fixture evidence, and RP6 report-card pilot evidence. | Hosted-provider behavior, commercial plugin-store behavior, or commercial local-agent behavior. |
| F4 Drift outcomes | `paper/figures/fig4-drift-outcomes.svg` | Contract checking separates realized violations, attempted overreach, missing outputs, canary observations, instrumentation failures, and runtime-pair disagreements before aggregate reporting. | Blocked attempts are successful defenses; missing outputs are security success; pairwise disagreement is ecosystem prevalence. |
| F5 Runtime report cards | `paper/figures/fig5-runtime-report-cards.svg` | Runtime report cards summarize realized violations, attempted overreach, missing outputs, benign task success, approval burden, utility cost, disagreements, instrumentation failures, and evidence coverage with explicit evidence-level labels. | RP6 defense success; RP1 hosted-provider behavior; RP5 commercial plugin behavior. |
| F6 Artifact flow | `paper/figures/fig6-artifact-flow.svg` | Release artifacts flow from tracked benchmark definitions to generated evidence, claim-ledger validation, verification, anonymity checks, and clean-bundle reproduction while raw scratch and human-review scaffolds remain bounded. | Completed human review, reviewer agreement, public-network exfiltration evidence, public release readiness, external review completion, or whole-repo archive readiness. |

## Current Placement

- `README.md` embeds the README-oriented copy of F1 and the existing
  result/flow summary figures for fast project orientation.
- The manuscript introduction can cite F1 and F4.
- The methodology section can cite F2 and F3.
- The evaluation and mitigation sections can cite F5.
- The artifact appendix can cite F6.

## Boundary Note

The figure package is a manuscript-structure artifact. It does not add new
experimental results. Every numerical claim still belongs in
`paper/claim-ledger.json`, and every evidence boundary still follows
`paper/tables/evidence-boundary-matrix.md`.
