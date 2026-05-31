# Paper Figure Package

The SVG files in this directory are the canonical paper-figure assets. PNG and
PDF exports, if created later, are derived artifacts and must not become the
source of truth.

## Figures

| Figure | File | Purpose |
| --- | --- | --- |
| F1 | `fig1-architecture.svg` | Method architecture and fixed-invariant/runtime-variable flow. |
| F2 | `fig2-trace-lifecycle.svg` | Trace lifecycle from run identity to claim-ledger-backed reports. |
| F3 | `fig3-runtime-matrix.svg` | Runtime-profile evidence levels and unsupported surfaces. |
| F4 | `fig4-drift-outcomes.svg` | Outcome taxonomy for contract findings and runtime-pair disagreements. |
| F5 | `fig5-runtime-report-cards.svg` | Runtime report-card dimensions and evidence-level labels. |
| F6 | `fig6-artifact-flow.svg` | Artifact-release flow and review/safety boundaries. |

## Boundary Rules

- Keep RP2/RP3 current executable evidence visually separate from RP1
  simulator-backed evidence, RP4/RP5 fixture evidence, and RP6 report-card
  pilot evidence.
- Do not use these figures to claim prevalence, commercial-runtime behavior,
  public-internet exfiltration, syscall-complete tracing, defense success,
  completed human review, reviewer agreement, or paper-grade benchmark
  completion.
- If a figure label or caption introduces a paper-facing number, add or update
  `paper/claim-ledger.json` and rerun `make verify`.

## Verification

The repository-wide verification path is still `make verify`. Before exporting
these figures, also parse the SVGs as XML and run the local-path scan.
