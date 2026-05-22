# Paper Claim Ledger

This ledger maps paper-facing claims to current repository evidence. The
machine-readable source of truth is `paper/claim-ledger.json`; validate it with:

```bash
python3 tools/validate_claim_ledger.py
```

## Claim Boundary

The current baseline evidence supports feasibility and method claims only. It does not support
ecosystem prevalence claims, commercial-runtime claims, full product execution
claims, public-internet testing claims, or syscall-complete tracing claims.

## Supported Numerical Claims

| Claim ID | Claim | Evidence |
| --- | --- | --- |
| CL-MVP-001 | Four controlled case families | `benchmark/manifests/skilldiff-mvp-baseline.json` |
| CL-MVP-002 | Twenty-four paper-facing canonical trace files | `benchmark/manifests/skilldiff-mvp-baseline.json` |
| CL-MVP-003 | Thirty tracked trace files including older smoke traces | `results/raw/*/trace.jsonl` |
| CL-MVP-004 | Five runtime-drift claims across RP2/RP3 | `benchmark/manifests/skilldiff-mvp-baseline.json` |
| CL-MVP-005 | Twenty-four pairwise disagreements across RP2/RP3 | `benchmark/manifests/skilldiff-mvp-baseline.json` |
| CL-MVP-007 | Two first-party seed case families: AuditLens and docs-forge | Baseline manifest |
| CL-MVP-008 | Two controlled synthetic case families: repo-audit and network-egress | Baseline manifest |
| CL-MVP-009 | Twelve RP2/RP3 comparison JSON files and twenty-four contract-finding JSON files | `results/mvp/*/*.json` |
| CL-MVP-010 | RP2/RP3 comparison artifacts have no unchecked comparator fields | `results/mvp/*/*_rp2_rp3_comparison.json` |
| CL-MVP-011 | First-party manifests publish verifier-required pinned source hash lists: 11 docs-forge entries and 42 AuditLens entries | First-party source manifests |
| CL-P1-001 | Paper spine freezes the top-tier thesis, RQs, threat model, reviewer risks, and venue backplan | `paper/paper-spine.md` |
| CL-CASE-001 | Repo-audit adversarial RP2/RP3 outcome counts | Baseline manifest and repo-audit result artifacts |
| CL-CASE-002 | Network-egress adversarial RP2/RP3 outcome counts | Baseline manifest and network-egress result artifacts |
| CL-CASE-003 | AuditLens contributes one drift claim and seven pairwise disagreements | Baseline manifest |
| CL-CASE-004 | docs-forge contributes two drift claims and eight pairwise disagreements | Baseline manifest |

## Boundary Claims

| Claim ID | Boundary |
| --- | --- |
| CL-MVP-006 | Current executable baseline comparisons are limited to RP2 and RP3. |
| CL-BOUNDARY-001 | Current baseline evidence is not ecosystem prevalence evidence. |
| CL-BOUNDARY-002 | Current baseline does not claim full docs-forge Node installer execution or full AuditLens product/live connector execution. |
| CL-BOUNDARY-003 | Current baseline does not claim public-internet testing, packet capture, DNS tracing, or syscall-complete host tracing. |
| CL-BOUNDARY-004 | Publishable artifacts use synthetic canaries only, do not retain raw payloads, and keep public internet contact outside the benchmark boundary. |
| CL-RQ-001 | Current baseline evidence supports RQ1/RQ4, partially supports RQ2, and does not yet answer RQ3/RQ5/RQ6. |

## Design Targets

| Claim ID | Target |
| --- | --- |
| CL-TARGET-001 | Full-paper evidence floor is at least 40 skills and 120 runs before repeats. |
| CL-TARGET-002 | Full-paper repeat plan is three repeats for deterministic controlled fixtures and five repeats for nondeterministic runs. |

## Maintenance Rule

Any paper text that adds or changes a number must add or update a claim-ledger
entry in `paper/claim-ledger.json`. The validator must run in `make verify`.
