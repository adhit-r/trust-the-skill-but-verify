# Provenance Next Steps

Worker C design note for the post-MVP trace harness phase. This document tracks provenance implementation options, trace fields, acceptance criteria, and risks around the RM-07 MVP evidence layer.

## Current Baseline

The current RM-07 harness emits normalized `trace.jsonl` events, process metadata, output manifests, canary observations, cleanup records, MVP Python-level `filesystem.read` events through `python_sitecustomize_wrapper_mvp` for controlled Python commands, PV-01 RP3 container-strace MVP `filesystem.read` events for `open`, `openat`, and `openat2` in container commands, PV-02 controlled fake-sink network events, and controlled semantic activation/approval/tool/persistence events for the MCP/tool workflow fixture.

The current evidence is useful for MVP contract checking, but it must not be described as syscall-complete, host-wide tracing, live MCP telemetry, commercial approval UX measurement, or complete persistence tracing. The next provenance phases should replace controlled semantic self-reporting with live fixture observers where needed while preserving the existing separation:

- Runtime profiles declare exposed capability and logging expectations.
- Adapters implement runtime mechanics and raw evidence collection.
- Trace normalization turns raw evidence into canonical events.
- Contract checking derives `allowed_by_contract`, attempted overreach, realized violations, and drift labels.

## Design Principles

1. Prefer bounded, reproducible instrumentation over broad host hooks.
2. Emit raw evidence first, then normalize to `trace.jsonl`.
3. Distinguish attempted, blocked, failed, and succeeded actions.
4. Never store sensitive payloads by default; hash and redact payloads unless a synthetic benchmark fixture explicitly opts in.
5. Treat instrumentation gaps as first-class artifacts, not silent absence.
6. Keep adapter support matrix explicit per runtime profile.
7. Keep source-only first-party provenance separate from runtime evidence; clean
   clone verification supports seed provenance, not runtime-drift claims.

## First-Party Source Provenance

### Target

Make the first-party seed boundary externally reproducible without vendoring
source trees. The current source-provenance phase verifies `adhit-r/docs-forge`
and `adhit-r/audit-lens` from clean ephemeral clones against the pinned commits,
trees, and published source-hash lists in their benchmark manifests.

### Current Artifact

```text
tools/verify_first_party_sources.py
experiments/first-party-source-provenance/reproduce_first_party_source_provenance.sh
benchmark/manifests/external-validity-scaffolds.json
results/external/first-party-source-provenance.json
results/external/first-party-source-provenance.md
tools/run_docs_forge_live_installer.py
tools/validate_docs_forge_live_installer.py
experiments/docs-forge-live-installer/reproduce_docs_forge_live_installer.sh
benchmark/manifests/docs-forge-live-installer.json
results/live/docs-forge-installer/dry_run_result.json
results/live/docs-forge-installer/dry_run_report.md
tools/run_docs_forge_live_project_local_install.py
tools/validate_docs_forge_live_project_local_install.py
experiments/docs-forge-live-project-local-install/reproduce_docs_forge_live_project_local_install.sh
benchmark/manifests/docs-forge-live-project-local-install.json
results/live/docs-forge-installer/project_local_install_result.json
results/live/docs-forge-installer/project_local_install_report.md
results/live/docs-forge-installer/project_local_install_trace.jsonl
tools/run_docs_forge_live_runtime_pair.py
tools/validate_docs_forge_live_runtime_pair.py
experiments/docs-forge-live-runtime-pair/reproduce_docs_forge_live_runtime_pair.sh
benchmark/manifests/docs-forge-live-runtime-pair.json
results/live/docs-forge-installer/project_local_runtime_pair_result.json
results/live/docs-forge-installer/project_local_runtime_pair_report.md
results/live/docs-forge-installer/project_local_runtime_pair_host_trace.jsonl
results/live/docs-forge-installer/project_local_runtime_pair_minimal_env_trace.jsonl
tools/run_docs_forge_live_package_observer.py
tools/validate_docs_forge_live_package_observer.py
experiments/docs-forge-live-package-observer/reproduce_docs_forge_live_package_observer.sh
benchmark/manifests/docs-forge-live-package-observer.json
results/live/docs-forge-installer/package_observer_result.json
results/live/docs-forge-installer/package_observer_report.md
results/live/docs-forge-installer/package_observer_trace.jsonl
tools/run_docs_forge_live_npx_observer.py
tools/validate_docs_forge_live_npx_observer.py
experiments/docs-forge-live-npx-observer/reproduce_docs_forge_live_npx_observer.sh
benchmark/manifests/docs-forge-live-npx-observer.json
results/live/docs-forge-installer/npx_observer_result.json
results/live/docs-forge-installer/npx_observer_report.md
results/live/docs-forge-installer/npx_observer_trace.jsonl
runtimes/docker/rp3-node/Dockerfile
tools/run_docs_forge_live_npx_rp3_node_observer.py
tools/validate_docs_forge_live_npx_rp3_node_observer.py
experiments/docs-forge-live-npx-rp3-node-observer/reproduce_docs_forge_live_npx_rp3_node_observer.sh
benchmark/manifests/docs-forge-live-npx-rp3-node-observer.json
results/live/docs-forge-installer/npx_rp3_node_observer_result.json
results/live/docs-forge-installer/npx_rp3_node_observer_report.md
results/live/docs-forge-installer/npx_rp3_node_observer_trace.jsonl
tools/run_docs_forge_live_npx_runtime_pair.py
tools/validate_docs_forge_live_npx_runtime_pair.py
experiments/docs-forge-live-npx-runtime-pair/reproduce_docs_forge_live_npx_runtime_pair.sh
benchmark/manifests/docs-forge-live-npx-runtime-pair.json
results/live/docs-forge-installer/npx_runtime_pair_result.json
results/live/docs-forge-installer/npx_runtime_pair_report.md
results/live/docs-forge-installer/npx_runtime_pair_rp2_trace.jsonl
results/live/docs-forge-installer/npx_runtime_pair_rp3_trace.jsonl
```

### Boundary

- The first-party source-provenance artifact is source provenance only.
- The docs-forge live-installer dry-run evidence exercises only help, version,
  and dry-run installer surfaces.
- The docs-forge project-local installer evidence executes one non-dry-run
  project-local install command against a disposable target and allows only
  expected target skill/playbook writes.
- The docs-forge live runtime-pair scaffold executes the same project-local
  installer command under host-environment and minimal-environment
  synthetic-home Node profiles and compares output and target mutation hashes.
- The docs-forge live package observer materializes the pinned local npm package
  with lifecycle scripts disabled and records the tarball boundary.
- The docs-forge live local-tarball npx observer executes `docs-forge --help`
  through `npx --offline --package <local tarball>`.
- The docs-forge RP3 Node container observer executes the same local-tarball
  npx help workload under Docker network denial and read-only root filesystem
  constraints.
- The docs-forge live npx runtime-pair scaffold compares the host Node
  synthetic-home observer and RP3 Node container observer on required safety
  invariants for the benign help workload.
- It does not execute public registry acquisition, package-name
  `npx docs-forge`, the Codex marketplace command, package install behavior,
  user-scope/global installation, or docs generation.
- It does not execute the full AuditLens product, connector auth flows, or live
  SaaS exports.
- It is excluded from MVP runtime-drift counts until live traces and
  comparisons exist.

### Current Live-Evidence Gate

The disposable docs-forge live-installer pilots now run the real Node CLI
help/version/dry-run surfaces and one project-local non-dry-run install against
a temporary target workspace. The project-local gate uses Node filesystem-call
instrumentation plus source, target, and synthetic-home pre/post checks. The
current live-evidence gate also compares host-environment and
minimal-environment synthetic-home Node project-local installs with matching
target/output hashes and no source/home mutations. It also materializes the
pinned local npm package through an offline `npm pack --ignore-scripts`
observer and runs docs-forge help through a local-tarball `npx --offline`
observer. The current gate also runs that local-tarball npx workload inside a
Node-capable RP3-derived container with Docker `--network=none` and
`--read-only`, then compares host Node and RP3 Node local-tarball npx evidence
with zero required pair-check failures. The next gate is a public-registry
observer with explicit network capture, or adversarial npx/package-acquisition
variants, before real docs-forge evidence can support package-acquisition or
runtime-drift claims.

## Syscall-Level File-Read Provenance

### Target

Capture RP3 container file-read attempts that bypass Python `sitecustomize`, including native tools, subprocesses, bundled scripts, shell utilities, and language runtimes other than Python. PV-01 covers a container `strace` MVP for `open`, `openat`, and `openat2`; it is not full syscall completeness across all runtimes.

### Implementation Options

| Option | Profiles | Mechanism | Strength | Limits |
| --- | --- | --- | --- | --- |
| Linux container syscall trace | RP3 first, RP6 later | Run workload under `strace -f -e trace=open,openat,openat2,readlink,stat,statx,access` inside the container | Best near-term syscall evidence with low host risk | Linux-specific; noisy; may require image support and ptrace capability |
| macOS process trace | RP2 optional | Use `fs_usage` or Endpoint Security-style observer outside the MVP path | Better local host coverage | Harder permissions story; lower reproducibility; may require user approval |
| LD_PRELOAD shim | RP3/RP6 controlled images | Interpose `open`, `openat`, `fopen`, `readlink`, selected libc calls | Low overhead for known images | Bypassed by static binaries, direct syscalls, non-libc paths |
| Language wrappers | RP2/RP3 fallback | Node, Python, shell wrapper hooks for common commands | Easy to integrate incrementally | Not complete and should remain labeled wrapper-level |

Phase status:

1. PV-01: RP3 container `strace` MVP is implemented for `open`, `openat`, and `openat2` read-like events in container commands.
2. RP2 remains on wrapper-level provenance until a local host observer is explicitly enabled.
3. `instrumentation_status.json` should continue to declare `filesystem_read_level` as one of `none`, `wrapper`, `syscall_container`, or `host_observer`.

### Raw Evidence

Add or extend per-run raw files:

```text
file_read_events.jsonl
syscall_file_events.jsonl
instrumentation_status.json
```

Suggested raw event fields:

```json
{
  "source": "strace",
  "pid": 123,
  "ppid": 1,
  "argv_hash": "sha256:...",
  "syscall": "openat",
  "path": "./.env",
  "path_resolution": "workspace_relative",
  "flags": ["O_RDONLY"],
  "status": "succeeded",
  "errno": null,
  "timestamp": "2026-05-20T00:00:00Z",
  "payload_hash": null,
  "redacted": true
}
```

Canonical normalized event mapping:

- `open`, `openat`, `openat2`: `filesystem.read` when observed by the RP3 container-strace MVP as read-like opens
- successful `fopen`: `filesystem.read` only when captured by a wrapper/interposition layer that observes it directly
- `readlink`, `stat`, `access`: `filesystem.metadata`
- failed denied path lookup: `filesystem.read` with `status: failed` only when the intent is a read-like open; otherwise `filesystem.metadata`

### Acceptance Criteria

- RP3 live runs can detect a non-Python command reading `./.env` through container-strace MVP evidence.
- RP3 live runs can distinguish a failed denied read from a succeeded read for supported `open`, `openat`, and `openat2` events.
- Trace events include process correlation for the reading process.
- Validation fails if a profile declares syscall read tracing but `instrumentation_status.json` says it was unavailable.
- The docs keep RP2 local tracing claims weaker unless a host observer is explicitly enabled.

### Risks

- `strace` can change timing and may not be available in minimal images.
- Ptrace permissions may conflict with non-root container hardening.
- Syscall traces are noisy; normalization must filter metadata probes from content reads.
- Path resolution across mounts must be deterministic or violations may be misclassified.

## Network Attempt Capture

### Target

PV-02 now has an MVP controlled-network evidence path without allowing real exfiltration. It has two implemented paths for controlled Python benchmark commands:

- An in-process fake HTTP sink for explicit reserved benchmark destinations such as `sink.rp2.invalid`.
- RP3 blocked-egress evidence for the same task family when the Docker profile denies outbound network access with `--network=none`.

The current claim is narrow: PV-02 proves fake-sink and blocked-egress provenance for controlled Python `urllib` benchmark runs. It does not prove packet capture, DNS tracing, arbitrary HTTP-client interception, or public-internet testing.

Hard safety boundary:

- Public internet is not contacted by benchmark network tests.
- External-looking benchmark domains must resolve or route only to loopback, an in-process fake sink, or a reserved invalid domain used for a blocked attempt.
- Request bodies, query strings, and sensitive headers are not stored raw in PV-02 artifacts.
- Payloads are represented by hashes, redaction flags, byte counts, and canary-label observations.
- Synthetic canaries are allowed; real secrets or live credentials are not.

### Implementation Options

| Option | Profiles | Mechanism | Strength | Limits |
| --- | --- | --- | --- | --- |
| Fake sink shim | RP2/RP3/RP6 | Route explicit reserved test domains to an in-process fake sink for controlled Python commands | Captures request metadata and canary presence safely | Python `urllib` MVP only; other clients need wrappers or lower-level capture |
| Container network deny plus trace | RP3 | Use `--network=none` or the profile-equivalent network-deny path and record failed resolver/connect attempts where available | Shows blocked attempts without public internet contact | Limited payload visibility |
| Egress wrapper | RP2/RP3 | Wrap `curl`, `wget`, Node fetch scripts, Python requests in benchmark commands | Useful for controlled tasks | Not complete |
| DNS sink | RP3/RP6 | Controlled resolver logs queried hostnames | Detects domain attempts | No body metadata |

Recommended phase order:

1. Done for the controlled Python MVP: fake-sink `POST` evidence for reserved domains such as `sink.rp2.invalid`.
2. Done for the controlled Python MVP: RP3 blocked-network evidence for the same benchmark attempt under Docker network denial.
3. Done for the controlled Python MVP: successful fake-sink sends and blocked attempts normalize into `network.send` or `network.connect` events with status.
4. Done for the controlled Python MVP: validation requires redacted or hashed payload metadata and rejects public-internet contact markers.

### Raw Evidence

```text
network_events.jsonl
network_sink_requests.jsonl
dns_events.jsonl
network_policy.json
```

Suggested normalized fields:

- `event_type`: `network.connect` or `network.send`
- `destination_host`
- `destination_port`
- `destination_kind`: `fake_sink`, `reserved_invalid`, `loopback`, `external`, or `unknown`
- `protocol`
- `method`
- `path_hash`
- `payload_hash`
- `payload_redacted`
- `payload_byte_count`
- `sensitive_headers_redacted`
- `canary_labels_observed`
- `status`: `attempted`, `blocked`, `failed`, or `succeeded`
- `sink_type`: `fake_http`, `dns`, `external_http`, `loopback`, or `unknown`
- `public_internet_contacted`: boolean
- `evidence_source`: `fake_sink`, `adapter_network_deny`, `syscall_trace`, `wrapper`, `dns_sink`, or `unknown`

### Acceptance Criteria

- Done for controlled Python MVP: a task that attempts `POST` to the fake sink produces a `network.send` event with `sink_type: fake_http`, `status: succeeded`, payload hash, redaction marker, byte count, evidence reference, and canary labels when synthetic canaries are present.
- Done for controlled Python MVP: the fake-sink test contacts only the in-process sink. Public internet contact is a validation failure.
- Done for controlled Python MVP: a task that attempts egress under RP3 network denial produces failed `network.connect` and `network.send` events, and no successful public-internet event.
- Done for controlled Python MVP: network payloads are redacted and represented by hashes or summaries in PV-02 artifacts.
- Done for controlled Python MVP: trace validation fails if a network send lacks `payload_hash`, if network payloads are not redacted, if raw payload fields are retained in metadata, or if a benchmark trace marks `public_internet_contacted: true`.
- Done for controlled Python MVP: contract checking counts blocked network attempts as attempted overreach and successful fake-sink sends as realized data-flow events when the contract denies the sink.
- Remaining boundary: do not generalize PV-02 beyond controlled Python benchmark commands until other clients, packet capture, DNS tracing, or syscall-level network provenance are implemented.

### Risks

- Some tools ignore proxy variables and need lower-level interception.
- DNS-only observations can overstate intent if software performs speculative lookups.
- Capturing payload hashes must avoid logging raw synthetic secrets.
- RP3 blocked-egress traces may prove that an attempt was blocked without exposing request-body metadata; that should be reported as a provenance limit, not a missing violation.

## Approval Trace Expansion

### Target

Make approval semantics comparable across runtimes by recording what action required approval, what prompt would be shown, what decision was made, and whether execution was gated on that decision.

### Event Model

Recommended canonical events:

- `approval.requested`
- `approval.decision`
- `approval.bypassed`
- `approval.not_required`

Required correlation fields:

- `approval_id`
- `correlated_event_id`
- `sensitive_action_type`
- `target_summary`
- `risk_label`
- `prompt_fields_present`
- `decision`: `allow`, `deny`, `auto_allow`, `auto_deny`, or `not_required`
- `decision_source`: `deterministic_shim`, `runtime_ui`, `profile_policy`, or `adapter_default`
- `gated_execution`: boolean

### Acceptance Criteria

- Every shell, network, mutating tool, persistence, or credential event can be correlated with either an approval decision or an explicit no-approval-required event.
- Deterministic approval shims emit the same decision for the same run spec and profile policy.
- A denied approval prevents the sensitive event from succeeding.
- Approval bypass can be represented without pretending a real UI prompt occurred.

### Risks

- Approval prompts differ by host UX and may not expose the same fields.
- A deterministic shim can miss social-engineering effects of real approval copy.
- Over-approximating approval requirements may inflate approval burden metrics.

## Tool Call Trace Expansion

### Target

Capture tool and MCP-style calls as security-relevant actions, not only shell commands.

### Event Model

Recommended canonical events:

- `tool.call`
- `tool.result`
- `tool.mutation`
- `tool.descriptor.read`
- `tool.install_hook`

Required fields:

- `tool_id`
- `tool_namespace`
- `tool_version`
- `descriptor_hash`
- `arguments_hash`
- `arguments_redacted`
- `mutation`: boolean
- `external_effect`: boolean
- `result_hash`
- `canary_labels_observed`
- `approval_id`

### Acceptance Criteria

- RP4 fixture tools can emit deterministic `tool.call` and `tool.result` events.
- Mutating tools are distinguishable from read-only tools.
- Tool arguments and results are hashed/redacted by default.
- Contract rules can allow or deny tool calls by namespace, tool ID, mutation flag, and sink type.

### Risks

- Tool descriptors can be prompt content, policy content, and executable authority at the same time.
- Connector-backed tools may expose real user data; benchmark mode must use fixtures only.
- Tool result redaction can hide canary propagation unless canary scanning runs before redaction.

## Persistence Trace Expansion

### Target

Track state that survives beyond the intended task boundary, including hidden files, plugin storage, caches, memory, and tool-maintained state.

### Event Model

Recommended canonical events:

- `persistence.write`
- `persistence.read`
- `persistence.delete`
- `persistence.retained`
- `persistence.cleanup`

Required fields:

- `store_type`: `file`, `plugin_storage`, `mcp_resource`, `memory`, `database`, or `unknown`
- `path_or_key_hash`
- `workspace_relative_path`
- `retention_scope`: `run`, `workspace`, `profile`, `user`, or `unknown`
- `post_cleanup_allowed`
- `cleanup_observed`
- `content_hash`
- `canary_labels_observed`

### Acceptance Criteria

- Writes to `.skill-cache/**` can be represented as persistence events separate from ordinary output writes.
- Cleanup can report retained state after the run.
- Persistent state containing canaries is detectable without storing raw content.
- Contract checking can report `persistence_violation_rate` as a D4 subtype.

### Risks

- File diffs alone cannot distinguish intended output from persistent state without contract sink metadata.
- Runtime memory or plugin storage may not be inspectable after execution.
- Cleanup may remove evidence before collection unless ordering is enforced.

## Cross-Surface Trace Validation

Add validator checks after the raw evidence paths exist:

- One `instrumentation_status.json` per run.
- Profile-declared instrumentation surfaces have matching raw evidence files or explicit unavailable status.
- Sensitive event types include approval correlation or explicit no-approval-required markers.
- Network payload fields are redacted or hashed for PV-02, and tool payload fields are redacted or hashed unless a later fixture explicitly opts in.
- Persistence events include retention scope and cleanup result.
- Canary observations are attached to sinks, not only to raw logs.

## Suggested Implementation Milestones

| Milestone | Scope | Exit Condition |
| --- | --- | --- |
| PV-01 | RP3 container-strace file-read MVP | Done for container `open`, `openat`, and `openat2` read-like events producing normalized `filesystem.read` with process correlation |
| PV-02 | Fake network sink and RP3 blocked egress | Done for controlled Python MVP: fake-sink `POST` produces redacted `network.send` and `network_sink_requests.jsonl` with payload hash and canary labels, and RP3 network denial produces failed `network.connect` / `network.send` without public internet contact |
| PV-03 | Approval correlation | Shell, network, tool, persistence, and credential events have approval linkage |
| PV-04 | RP4 tool fixtures | Deterministic tool calls and tool results appear in traces |
| PV-05 | Persistence retention | Hidden state writes and retained post-cleanup state are normalized and checkable |

## Non-Goals For This Phase

- No claim of complete commercial-runtime observability.
- No real credential collection.
- No public internet exfiltration.
- No host-wide macOS tracing by default.
- No changes to the D1-D5 taxonomy; persistence remains a separately reported D4 subtype.
