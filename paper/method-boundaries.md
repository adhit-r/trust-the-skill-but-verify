# Method Boundaries

This file records reviewer-safe wording for the current method and artifact
state. Use it before turning the MVP artifacts into paper prose.

## What Current Evidence Supports

- The same skill-task-contract pair can produce different observed security
  outcomes under RP2 and RP3 when repeat ID, workspace snapshot, task prompt,
  and variant ID are also held fixed.
- The framework can distinguish benign controls from adversarial variants in
  the current controlled fixtures.
- Realized violations and attempted overreach are separate measurements.
- Synthetic canary movement can be observed in generated reports, dashboards,
  logs, and changed files.
- Fake-sink network egress and blocked RP3 network attempts can be measured
  without contacting the public internet.
- First-party seed repos can be pinned and transformed into publishable
  controlled fixtures without vendoring full source trees.

## What Current Evidence Does Not Prove

- It does not prove that all agent skills are unsafe.
- It does not prove real-world prevalence.
- It does not execute the real docs-forge Node installer.
- It does not execute the full AuditLens product or live connectors.
- It does not include public-internet testing.
- It does not include packet capture, DNS tracing, or arbitrary HTTP-client
  interception.
- It does not provide syscall-complete host tracing.
- It does not cover commercial hosted runtimes.
- It does not yet measure MCP tool calls, approval bypass, connector auth, or
  hidden persistence completely.

## Provenance Levels

| Level | Current Artifact | Safe Description | Unsafe Description |
| --- | --- | --- | --- |
| RP2 Python reads | `python_sitecustomize_wrapper_mvp` | Python wrapper-level file-open evidence for controlled Python commands | Syscall-complete host tracing |
| RP3 file reads | `container_strace_mvp` | Container `open`, `openat`, and `openat2` evidence for supported runs | Full container or host filesystem telemetry |
| Writes and outputs | Workspace diff and output manifests | Observed output and mutation evidence | Complete persistence tracing |
| Network | Fake sink and Docker network denial | Controlled fake-sink and blocked-egress evidence | Packet capture or public-internet measurement |
| Canaries | Output/log/change scanning | Synthetic canary movement in observed sinks | Real secret exfiltration evidence |

## Network Evidence Boundary

Benchmark network tests must not contact the public internet. RP2 fake-sink
runs record payload hashes, byte counts, redaction flags, and canary labels.
RP3 blocked-egress runs record denied destinations and failed or blocked
network status. Raw request bodies, raw query strings, sensitive headers, and
real secrets are outside the safe artifact boundary.

## Approval, Tool, and Persistence Gaps

Approval prompts, MCP tool calls, connector auth checks, and hidden persistence
are part of the broader roadmap but are not completed by the current MVP. The
paper can name them as future measurement axes or planned benchmark categories,
but current results should not count them as evaluated.

## Reviewer-Safe Claim

We introduce differential runtime security testing for portable agent skills:
given a skill, task, contract, fixed task prompt, fixed workspace snapshot,
variant, repeat ID, and runtime profile, the framework executes controlled
benign and adversarial variants, records normalized traces, and compares
whether violations are realized, blocked, or converted into missing outputs
across runtimes. In the current MVP, four controlled case families produce five
runtime-drift claims across RP2 and RP3, while preserving explicit boundaries
around provenance, network evidence, product execution, and safe publication.

## Reviewer-Risky Wording To Avoid

- "The benchmark proves agent skills are unsafe."
- "The Docker runtime prevents all leakage."
- "The trace harness captures every file read."
- "Network exfiltration was observed on the internet."
- "docs-forge was fully executed."
- "AuditLens connector behavior was evaluated."
- "Approval drift is measured in the current MVP."
