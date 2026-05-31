# Evidence Boundary Matrix

This table is the paper-facing boundary map for current evidence, promoted
bounded evidence, and future work. It is intentionally conservative: a row is
claimable only to the level named in the "Paper-safe use" column.

## Evidence States

| Evidence State | Meaning | Paper-Safe Use |
| --- | --- | --- |
| Current executable evidence | Validated traces, contract findings, and comparisons exist for the stated runtime profiles and fixtures. | Use for bounded method and measurement claims. |
| Promoted bounded evidence | Previously planned or supplemental artifacts now have controlled fixture, simulator, report-card, repeat, or interval artifacts. | Use only with simulator/fixture/source-only/report-card labels visible. |
| Review-ready scaffold | Queue, packet, blinded bundle, or blank template exists, but no completed independent human labels exist. | Use to show artifact readiness, not agreement or adjudication. |
| Future work | Required for top-tier full-paper strength but not yet evidenced. | Mention as a gate, limitation, or next step only. |

## Paper Claim Matrix

| Component | Evidence State | Paper-Safe Use | Must Not Claim | Next Gate |
| --- | --- | --- | --- | --- |
| RP2/RP3 MVP drift baseline | Current executable evidence | Five controlled case families, twenty-eight paper-facing canonical traces, five runtime-drift claims, and thirty-six pairwise disagreements support the core differential-conformance method. | Ecosystem prevalence, commercial-runtime behavior, or universal runtime safety. | Scale the same invariant-preserving comparison beyond the current controlled slice. |
| Benchmark manifest and source mix | Promoted bounded evidence | The current manifest records forty-four skills and one hundred thirty-two skill-task-contract triples, with source-origin accounting at nine first-party, seventeen public, and eighteen synthetic skills. | Source-mix evidence completion or full-paper execution completion. | Promote more first-party/public source-provenance entries into executable evidence. |
| Selected source-mix controlled fixtures | Promoted bounded evidence | Seventy-two selected first-party/public source-mix cases have controlled RP2/RP3 fixture evidence across twenty-four families, with zero current source-mix metadata-only cases. Seventy-four first-party/public source-mix cases across twenty-six families also have bounded deterministic source-mix RP6 repeat mitigation/report-card evidence. | Live product behavior, public-network behavior, commercial-runtime behavior, defense success, or source-mix completion. | Source-mix completion remains blocked on reviewer adjudication and selective safe task-specific real-run evidence. |
| Planned-inclusion fixture promotion | Promoted bounded evidence | One hundred sixteen formerly planned entries now have controlled single-repeat RP2/RP3 fixture comparisons and trace-backed contract findings. | Runtime-drift findings for the promoted batch or skill-specific live product behavior. | Add broader profile execution and task-specific real-run adapters where safe. |
| Planned-inclusion deterministic repeats | Promoted bounded evidence | The one hundred sixteen promoted controlled fixtures have repeat IDs 1, 2, and 3, producing six hundred ninety-six trace-valid observations and three hundred forty-eight same-repeat RP2/RP3 pairs. | Model-mediated stability, prevalence, or reviewer-agreement claims. | Add repeat support to remaining profile-specific and nondeterministic runners. |
| Gate 5 descriptive denominator | Promoted bounded evidence | The frozen Gate 5 table includes one hundred thirty-two cases and the descriptive artifact reports twenty-two raw inventory and coverage rate records. | Confidence intervals, hypothesis tests, reviewer agreement, or prevalence from the descriptive artifact itself. | Keep interval and review artifacts separate and validator-backed. |
| Gate 5 non-human intervals | Promoted bounded evidence | The machine-only interval artifact reports thirty-six Wilson intervals, eighteen case-bootstrap intervals, six hierarchical skill/case bootstrap intervals, and paired-runtime majority, median, and max-severity summaries over two hundred fourteen pair records. | Human review, adjudication, McNemar-style hypothesis tests, prevalence, source-mix completion, or paper-grade completion. | Add binary matched outcome labels before McNemar-style tests. |
| Runtime report cards | Promoted bounded evidence | RP1, RP2, RP3, RP5, and RP6 have deterministic report cards, summarized in `paper/tables/runtime-report-card-summary.md`; RP1 is simulator-backed, RP5 is fixture-backed, and RP6 includes bounded current-case and bounded deterministic source-mix repeat mitigation/report-card evidence. | Hosted-provider behavior, commercial plugin-store behavior, product-scale defense success, source-mix completion, or RP6-vs-RP2/RP3 runtime-drift claims. | Report-card and source-mix completion remain blocked on reviewer adjudication and selective safe real-run evidence. |
| Static and least-privilege baselines | Promoted bounded evidence | Static scanner, reachability approximation, action-boundary, least-privilege, mitigation-ladder, and RP6 ablation artifacts can be used as bounded comparator or strengthening evidence. | Semia equivalence, ClawGuard or Task Shield reproduction, live guardrail efficacy, or vulnerability prevalence. | Add broader runtime-backed baseline comparisons where evidence supports them. |
| Human review queue and packet exports | Review-ready scaffold | The queue, packet index, blinded packet bundle, and two blank review templates show that the current artifacts can be sent to reviewers. | Completed human review, reviewer identities, percent agreement, Cohen's kappa, adjudication, or Codex-assisted labels counted as human labels. | Real independent reviewers must complete the exported templates. |
| Related work and venue positioning | Promoted bounded evidence | The related-work map was refreshed from current primary arXiv, MCP, and OWASP sources on 2026-05-28 and can support positioning text. | Firstness, prevalence, Semia-equivalence, live-guardrail, public-network, commercial-runtime, defense-success, or completed-human-review claims. | Recheck primary paper versions, official specs, OWASP pages, and venue CFPs immediately before submission text freezes. |
| Artifact release package | Promoted bounded evidence | A curated local machine-only bundle path and one-command table reproduction path now exist, with release manifests, checksums, and bundle validation in `make verify`. | Whole-repo archive readiness, public release readiness, external review completion, raw scratch publication, completed human review, or paper-grade completion. | Test from a clean checkout and update venue-specific artifact instructions before external submission. |

## Runtime Report-Card Boundary

| Runtime Profile | Current Paper Role | Evidence Level | Safe Wording | Unsafe Wording |
| --- | --- | --- | --- | --- |
| RP1 restricted-hosted | Simulator-backed hosted-style contrast for upload-oriented current cases. | Deterministic simulator report card. | "RP1 simulator-backed evidence." | "Hosted-provider behavior" or "commercial hosted runtime coverage." |
| RP2 local adapter | Primary local controlled-execution comparison profile. | Current executable evidence and report-card aggregation. | "RP2 local controlled fixture evidence." | "Commercial local-agent behavior." |
| RP3 Docker adapter | Primary sandboxed controlled-execution comparison profile. | Current executable evidence and report-card aggregation. | "RP3 Docker-backed sandbox evidence for supported traces." | "All container behavior is syscall-complete" or "Docker prevents unsafe behavior." |
| RP4 MCP-connected | Bounded local MCP descriptor/resource/tool fixture. | Fixture-only MCP evidence. | "Bounded local MCP fixture evidence." | "External MCP server, connector-auth, or commercial MCP-client behavior." |
| RP5 plugin-style | Local plugin lifecycle and activation fixture. | Fixture-backed plugin report card. | "Fixture-backed plugin-style evidence." | "Commercial plugin-store or live host API behavior." |
| RP6 policy-hardened | Mitigation/report-card pilot and component-ablation subject. | Bounded report-card and ablation evidence. | "Policy-hardened report-card evidence with utility cost reported." | "Defense success" or "product-scale causal mitigation proof." |

## Submission Use

Use this matrix to keep manuscript tables and prose in three buckets:

- Current evidence: direct, validated execution or generated artifact evidence.
- Promoted bounded evidence: useful for full-paper direction, but labeled as
  simulator, fixture, source-only, report-card, repeat, or machine-only
  interval evidence.
- Future work: necessary before top-tier submission claims, especially real
  human review, adjudication, broader executable evidence, source-mix
  promotion, and clean venue-specific artifact submission checks.
