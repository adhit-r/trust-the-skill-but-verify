# Adapter Support Matrix

This matrix is the current per-surface evidence map for SkillDiff runtime
profiles. It is a steering document for S1 in `research-roadmap.md`: make the
runtime variable unignorable before scaling the benchmark.

## Support States

Use these exact states when updating the matrix:

| State | Meaning |
| --- | --- |
| `implemented` | The current verified artifact emits normalized evidence for this surface, and the evidence can support bounded paper claims. |
| `simulated` | The runtime profile or deterministic simulator defines the behavior, but the surface does not yet have promoted live execution evidence. |
| `fixture-only` | A controlled fixture emits semantic or wrapper evidence, but the result is not live host, live MCP, live connector, or commercial-runtime evidence. |
| `unavailable` | The surface is planned or relevant, but the current adapter does not yet produce usable evidence. |
| `intentionally-unsupported` | The profile disables this surface by design; claims should say the surface is out of scope or denied by profile policy. |

## Instrumentation-Failure Rule

Missing observer coverage is not security success. If a profile enables a
surface, or a paper claim depends on that surface, but the adapter does not
emit capability and trace evidence for it, record an instrumentation failure
or keep the claim out of the paper. This applies especially to activation,
approval, tool/MCP, persistence, host filesystem reads, and network behavior.

## Current Matrix

| Profile | Evidence Level | Filesystem Reads | Filesystem Writes | Process / Shell | Network | Activation | Approval | Tool / MCP | Persistence | Context | Cleanup | Canary Observation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RP1 restricted hosted | Promoted deterministic simulator evidence | `simulated` | `simulated` | `intentionally-unsupported` | `intentionally-unsupported` | `simulated` | `simulated` | `simulated` | `intentionally-unsupported` | `simulated` | `simulated` | `simulated` |
| RP2 local coding agent | Verified MVP runtime | `implemented` | `implemented` | `implemented` | `fixture-only` | `fixture-only` | `fixture-only` | `fixture-only` | `fixture-only` | `implemented` | `implemented` | `implemented` |
| RP3 Docker sandbox | Verified MVP runtime | `implemented` | `implemented` | `implemented` | `implemented` | `fixture-only` | `fixture-only` | `fixture-only` | `fixture-only` | `implemented` | `implemented` | `implemented` |
| RP4 MCP-connected | Bounded fixture evidence (S1.2) | `fixture-only` | `fixture-only` | `intentionally-unsupported` | `intentionally-unsupported` | `fixture-only` | `fixture-only` | `fixture-only` | `fixture-only` | `fixture-only` | `fixture-only` | `fixture-only` |
| RP5 plugin-style | Bounded plugin fixture evidence (S1.4) | `fixture-only` | `fixture-only` | `fixture-only` | `intentionally-unsupported` | `fixture-only` | `fixture-only` | `fixture-only` | `fixture-only` | `fixture-only` | `fixture-only` | `fixture-only` |
| RP6 policy-hardened | Current-case report-card pilot (S1.3) | `fixture-only` | `fixture-only` | `fixture-only` | `fixture-only` | `fixture-only` | `fixture-only` | `fixture-only` | `fixture-only` | `fixture-only` | `fixture-only` | `fixture-only` |

## Profile Notes

### RP1 Restricted Hosted

RP1 is a restricted hosted-style comparison profile. It models upload-only
files, no shell, no network, no ambient credentials, deterministic approvals,
and ephemeral state. RP1 now has promoted deterministic simulator evidence for
a restricted-hosted-style profile over the upload-oriented current-case subset.
It is simulator-backed evidence only: no real hosted provider, commercial
assistant, live connector authorization, live MCP/plugin behavior, or
public-network behavior is claimed.

Current status: `restricted_hosted_sim` emits valid RP1 traces and
`results/fixtures/rp1-restricted-hosted/report_card.json` reports the utility
cost explicitly. The current subset excludes MCP/tool workflow because the RP1
profile disables MCP/plugin APIs. Missing outputs and blocked unsupported
surfaces are coverage/utility costs, not defense-success evidence.

### RP2 Local Coding Agent

RP2 is part of the verified MVP evidence. It currently supports copied
workspace execution, subprocess metadata, output manifests, pre/post file
observations, Python wrapper-level file-read provenance for controlled Python
commands, fake-sink network evidence for controlled Python paths, deterministic
semantic approval events in fixtures, and canary scanning over files, outputs,
logs, and network metadata.

Boundaries:

- Not syscall-complete host tracing.
- Not arbitrary HTTP-client interception.
- Not live commercial local-agent evidence.
- Tool, approval, activation, and persistence evidence is fixture-level unless
  a specific runner says otherwise.

### RP3 Docker Sandbox

RP3 is part of the verified MVP evidence. It currently supports Docker-backed
execution, read-only source mounts, writable output mounts, no-network runs,
container process metadata, output manifests, blocked network evidence,
Python wrapper-level events for controlled Python commands, and
container-strace MVP file-read evidence for supported `open`, `openat`, and
`openat2` events.

Boundaries:

- Not host-wide tracing.
- Not syscall-complete tracing for every container behavior.
- Not packet capture or DNS tracing.
- Tool, approval, activation, and persistence evidence is fixture-level unless
  a specific runner says otherwise.

### RP4 MCP-Connected

RP4 now has a bounded S1.2 local MCP fixture. It is the first promoted
MCP/tool-resource execution surface, but it remains fixture evidence rather
than commercial-client or external MCP-server evidence. The promoted fixture
emits:

- `activation.*` events for skill selection and non-selection.
- `approval.*` events for allowed and denied tool/resource operations.
- `tool.call` and MCP-specific metadata for allowed and denied calls.
- MCP resource-read and tool-result evidence.
- Synthetic token/canary handling.
- Capability snapshots that list servers, tools, resources, and auth mode.
- Cleanup evidence for session state.

This supports only local fixture claims. RP4 must still not be used for
external MCP server, connector-auth, commercial-client, public-network, or
runtime-drift claims.

### RP5 Plugin-Style

RP5 now has a bounded S1.4 local plugin-style fixture. It measures fixture
plugin manifest parsing, activation selection, non-activation negative control,
install-hook execution metadata, bundled-resource reads, local update metadata,
fixture host API calls, scoped plugin storage, generated outputs, and cleanup.
Current artifacts:

- `src/skilldiff/adapters/plugin_fixture.py`
- `tools/run_rp5_plugin_fixture_mvp.py`
- `tools/validate_rp5_plugin_fixture_mvp.py`
- `results/fixtures/rp5-plugin-style/report_card.json`

This supports only local fixture claims. RP5 must still not be used for
commercial plugin-store behavior, live host API behavior, external MCP/server
behavior, public-network behavior, hidden plugin marketplace behavior, or
defense-success claims. The activation negative control records
`activation.not_selected` for an unrelated meeting-notes task, but this is not
live host activation telemetry.

### RP6 Policy-Hardened

RP6 is the mitigation/runtime-report-card profile. It should run the same
skill-task-contract triples as RP2/RP3 while enforcing contract-derived
allowlists for files, network, tools, approvals, and persistence. It should not
be treated as a defense success unless the report card also reports task
success, missing outputs, approval burden, and instrumentation coverage.

Current S1.3 status: `hardened_policy_adapter` runs the fourteen existing
current-case variants across repo-audit, network-egress, MCP/tool workflow,
AuditLens, and docs-forge. The verified report card is
`results/fixtures/rp6-policy-hardened/report_card.json`: zero realized
contract violations, twelve blocked attempted-overreach findings, seven
missing expected outputs, and zero canary observations. The report card also
includes one supplemental network-denial policy probe that records blocked
`network.connect` and `network.send` events without changing the fixed
current-case variants. RP6-vs-RP2/RP3 comparisons are labeled as mitigation
report-card contrasts, not runtime-drift claims. This remains wrapper-level
controlled Python and controlled semantic-fixture evidence, not syscall-complete
hardening, commercial-runtime behavior, or a defense-success claim.

## Claim Rules

| Surface | Paper-Safe Claim Rule |
| --- | --- |
| Filesystem reads | Claim only the specific observer level: wrapper-level, container-strace MVP, or future host observer. |
| Filesystem writes | Distinguish expected outputs, denied source mutation, failed write attempts, and cleanup residue. |
| Process / shell | Claim subprocess or container-command evidence only when command metadata and exit status are traced. |
| Network | Distinguish fake-sink sends, blocked-egress attempts, loopback-registry probes, and packet-capture evidence. |
| Activation | Do not claim host activation drift until activation-negative-control tasks and profile-specific selection traces exist. |
| Approval | Do not claim approval UX behavior from deterministic fixture events alone. |
| Tool / MCP | Do not claim external MCP server, connector-auth, or commercial-client behavior from the bounded RP4 local fixture. |
| Persistence | Do not claim persistence completeness until retained-state and cleanup-leftover semantics are traced. |
| Context | State whether context is copied workspace, mounted repo, selected fixture, uploaded files, or task-only. |
| Cleanup | Treat cleanup failure or retained state as D4 evidence, not as a generic run failure. |
| Canary Observation | Report canary movement only through scanned sinks: output files, logs, tool messages, network metadata, or persistence. |

## Next Promotion Gate

S1.4 is complete for bounded RP1/RP5 coverage when `make verify` validates the
RP1 simulator artifacts and RP5 plugin-style fixture artifacts. The next runtime
promotion gate is not another one-off fixture; it is either external MCP/client
measurement without real credentials or public-network exposure, or static and
action-boundary baselines that make the existing report cards reviewer-ready.
