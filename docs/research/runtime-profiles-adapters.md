# Runtime Profiles and Adapters

Working note for RM-06 of `Trust the Skill, Verify the Runtime`.

## Purpose and Boundary

Runtime profiles describe host policy and exposed capability. Security contracts describe task-allowed behavior. Trace normalization and metric computation are later phases.

The separation is intentional:

- Runtime profile: what the host exposes, blocks, logs, and cleans up.
- Security contract: what the task allows or denies.
- Adapter: how a profile is prepared, run, collected, and cleaned up.
- Trace harness: how raw adapter evidence becomes canonical `trace.jsonl`.

Adapters emit raw deterministic evidence plus a pre-run capability snapshot. They do not emit drift findings or contract decisions.

## Profile Schema

Runtime profiles use `schemas/runtime_profile.schema.json`. Every profile must define:

- `schema_version`
- `profile_id`
- `profile_version`
- `profile_name`
- `profile_semantics`
- `runtime_family`
- `adapter`
- `features`
- `reproducibility`

Runtime families:

| Family | Intended Profile |
| --- | --- |
| `restricted_hosted` | RP1 |
| `local_coding_agent` | RP2 |
| `docker_sandbox` | RP3 |
| `mcp_connected` | RP4 |
| `plugin_style` | RP5 |
| `policy_hardened` | RP6 |

Concrete profile files:

| Profile | File | Adapter |
| --- | --- | --- |
| RP1 | `runtimes/profiles/RP1_restricted_hosted.yaml` | `restricted_hosted_sim` |
| RP2 | `runtimes/profiles/RP2_local_coding_agent.yaml` | `local_adapter` |
| RP3 | `runtimes/profiles/RP3_docker_sandbox.yaml` | `docker_adapter` |
| RP4 | `runtimes/profiles/RP4_mcp_connected.yaml` | `mcp_fixture_adapter` |
| RP5 | `runtimes/profiles/RP5_plugin_style.yaml` | `plugin_fixture_adapter` |
| RP6 | `runtimes/profiles/RP6_policy_hardened.yaml` | `hardened_policy_adapter` |

Current per-surface support status is tracked in
`docs/research/adapter-support-matrix.md`. Treat that matrix as the source of
truth for which runtime surfaces are implemented, simulated, fixture-only,
unavailable, or intentionally unsupported before making paper claims.

Every profile includes these feature blocks, even when a feature is disabled:

| Feature Block | Purpose | Drift Surface |
| --- | --- | --- |
| `activation` | Discovery, routing, metadata trust, auto-activation | D1 |
| `filesystem` | Roots, mounts, symlink policy, read/write defaults | D2, D4, D5 |
| `shell` | Execution policy, allowlists, environment policy | D2, D3, D4 |
| `network` | Egress policy, fake sinks, loopback, DNS | D2, D3, D5 |
| `credentials` | Ambient credentials, synthetic secrets, token forwarding | D2, D5 |
| `context` | Prompt, files, workspace, chat history, memory, tool results | D1, D2, D5 |
| `persistence` | Stores, retention, cross-run state, cleanup expectations | D4, D5 |
| `approvals` | Prompt policy, deterministic decisions, transcript recording | D3 |
| `tools` | Tool availability, mutation policy, descriptor sources | D1, D2, D3, D4, D5 |
| `mcp_plugin_apis` | MCP/plugin resources, descriptor trust, install hooks | D1, D2, D4, D5 |
| `logging` | Event categories, payload capture, redaction, canary logs | D5 |
| `cleanup` | Workspace lifecycle, paths removed/preserved, failure cleanup | D4 |
| `instrumentation` | Monitors, canary scanner, capability snapshot, seed | All |

## RP1-RP6 Semantics

| Profile | Semantics |
| --- | --- |
| RP1 restricted hosted-style | Uploaded/task files only, no shell, no host credentials, no ambient workspace, no cross-run persistence |
| RP2 local coding-agent | Broad workspace context, shell available, local filesystem exposure, deterministic approval shim, weaker isolation |
| RP3 Docker sandbox | Explicit mounts, shell inside container, network disabled, synthetic credentials only, deterministic cleanup |
| RP4 MCP-connected | Tool/resource-rich runtime with MCP fixtures, descriptors, tool-message sinks, no real auth |
| RP5 plugin-style | Plugin discovery, activation metadata, install hooks, host API fixtures, plugin storage |
| RP6 policy-hardened | Contract-derived allowlists, strict cleanup, no ambient credentials, taint-aware sink restrictions |

RP2 and RP3 are the MVP execution pair. RP4 now has bounded S1.2 local MCP
fixture evidence, but it is not external MCP server, connector-auth, or
commercial-client evidence. RP6 now has a current-case report-card pilot through
`hardened_policy_adapter`, but it remains controlled Python and controlled
semantic-fixture evidence excluded from RP2/RP3 MVP aggregate counts. Its
comparison reports label RP6-vs-RP2/RP3 pairs as mitigation-report-card
contrasts, and the report card includes a supplemental network-denial policy
probe for direct blocked-connect/send evidence. RP1 now has deterministic
restricted-hosted simulator evidence for the upload-oriented current subset,
but it is not real hosted-provider, commercial assistant, live MCP/plugin, or
public-network evidence. RP5 remains a controlled profile for later matrix
expansion.

## Adapter Interface

The adapter interface has four lifecycle methods plus one required pre-run capability snapshot:

```text
prepare(run_spec, runtime_profile, workspace_seed, contract, task_prompt) -> PreparedRun
run(prepared_run) -> RunExecution
collect(prepared_run, run_execution) -> CollectedRun
cleanup(prepared_run, run_execution) -> CleanupResult
capability_snapshot(runtime_profile) -> capabilities.json
```

Required object boundaries:

| Object | Purpose |
| --- | --- |
| `PreparedRun` | Run ID, copied/mounted workspace, artifact directories, hashes, redacted env, approval shim config |
| `RunExecution` | Adapter outcome, timestamps, exit code, stdout/stderr paths, adapter event paths, process/container IDs |
| `CollectedRun` | Capability snapshot path, output manifest, raw trace sources, canary observations, approval transcript |
| `CleanupResult` | Removed paths, leftover state findings, post-cleanup observations, cleanup status |

Per run, adapters write deterministic raw evidence under:

```text
results/raw/<run_id>/
  run_metadata.json
  capabilities.json
  adapter_events.jsonl
  stdout.log
  stderr.log
  approvals.jsonl
  network_attempts.jsonl
  file_observations.jsonl
  outputs_manifest.json
  cleanup.json
```

RM-07 will normalize these files into canonical trace events. RM-06 adapters should not decide `allowed_by_contract`, `AV(x)`, `RV(x)`, or drift classes.

The concrete interface and dry-run MVP adapters live in:

- `src/skilldiff/adapters/base.py`
- `src/skilldiff/adapters/local.py`
- `src/skilldiff/adapters/docker.py`
- `tools/adapter_smoke.py`

RM-06 adapter smoke tests prove lifecycle and artifact-layout reproducibility only. They do not prove live runtime enforcement, process tracing, or Docker isolation. RM-07 adds controlled live execution, MVP Python-level read provenance, and PV-01 RP3 container-strace MVP read provenance for supported `open`, `openat`, and `openat2` container syscalls. Syscall-complete read tracing across all runtimes remains outside the current adapter claim.

## Local Adapter MVP

The local adapter is a controlled approximation of RP2, not a faithful implementation of any commercial local agent host.

MVP behavior:

- Copy a seed workspace into a fresh run directory during `prepare`.
- Redact ambient environment by default.
- Inject only synthetic benchmark canaries and benchmark-required variables.
- Emit a capability snapshot before execution.
- Capture process launch metadata, stdout/stderr, output manifests, and pre/post workspace file observations.
- Capture MVP Python-level file-read attempts for controlled Python commands through the read-provenance shim.
- Use deterministic approval-shim logs instead of live UI prompts.
- Mark local isolation strength as weaker than Docker.
- Defer host-level and broader runtime provenance to later RM-07/RM-09 work.

The local adapter must not execute in-place against benchmark seeds.

## Docker Adapter MVP

The Docker adapter is the RP3 isolation baseline.

Safe defaults:

- `--network=none`
- non-root execution
- read-only benchmark workspace mount
- writable output/artifact mount only where needed
- no ambient host credentials, SSH keys, Docker socket, or host home directory
- deterministic cleanup

These defaults are encoded in `runtimes/profiles/RP3_docker_sandbox.yaml` under `adapter.runtime_constraints`, not hidden in adapter code. The adapter derives both dry-run and live Docker invocation metadata from that profile block.

The Docker adapter emits mount manifests, container command metadata, stdout/stderr paths, output manifests, cleanup observations, MVP Python-level read events for controlled Python commands, and PV-01 `container_strace_mvp` file-read events for supported `open`, `openat`, and `openat2` container syscalls. The RM-07 live path copies the seed workspace, mounts it read-only, mounts a writable output workspace, and runs a pinned-image command when Docker is available. If Docker, the image, or the strace log is unavailable while syscall tracing is declared, validation fails instead of treating the run as evidence. It still does not claim host-wide tracing, syscall-complete file-read provenance across all runtimes, commercial runtime coverage, or packet-level network interception.

## Config vs Adapter Code

Profile config contains security policy:

- roots and mounts
- allowlists and denied surfaces
- fake sinks
- credential exposure
- approval semantics
- tool, MCP, and plugin fixtures
- logging and redaction
- cleanup behavior
- instrumentation toggles
- reproducibility pins

Adapter code contains mechanics:

- workspace creation
- mount/firewall/env application
- command construction
- approval shimming
- evidence logging
- hash computation
- cleanup execution
- unsupported-feature failures

Adapter code may enforce profile config, but must not silently add or remove security policy. If a runtime cannot implement a configured feature, it must fail closed and emit an instrumentation-failure artifact.

## Validation Invariants

Runtime profile validation fails when:

- Required top-level fields or feature blocks are missing.
- Unknown top-level fields are present.
- `profile_hash` does not match canonical profile content.
- Live external egress is enabled outside fake sinks or explicit safe test domains.
- Real host credentials are enabled.
- Writable roots exist without cleanup policy.
- Persistence is enabled without retention and post-cleanup semantics.
- Instrumentation is disabled for a surface the profile enables.
- MCP/plugin APIs are enabled without fixture hashes.
- Approval mode is unspecified for enabled shell, network, tool mutation, persistence, or credential exposure.
- Adapter declares support but cannot emit capability snapshots.
- Paths escape the run workspace unless explicitly marked as controlled external fixtures.
- RP6 hardening policy is hidden in adapter code rather than visible in config.

Warnings should flag broad workspace reads outside RP2, shell allow-all, network allow-all, chat history/runtime memory context, and full-payload logs.

The validator lives at `tools/validate_runtime_profiles.py`. It uses a deterministic local JSON Schema subset, validates benchmark-specific safety invariants, and checks canonical `sha256` profile hashes. The profile hash excludes only `reproducibility.profile_hash`, so policy edits force a hash update.

Validation commands:

```bash
python3 tools/validate_runtime_profiles.py --self-test runtimes/profiles/RP*.yaml
python3 tools/adapter_smoke.py
```

## Metric Mapping

Profiles supply enforcement facts; contracts decide compliance.

| Drift Class | Profile Inputs |
| --- | --- |
| D1 | activation, tools, MCP/plugin APIs, context |
| D2 | capability snapshots for filesystem, shell, network, credentials, context, tools |
| D3 | approvals, approval transcript, correlated sensitive actions |
| D4 | writes, shell/process execution, mutating tools, persistence, plugin storage, cleanup residue |
| D5 | credentials, context, canaries, sinks, network sends, tool messages, logs, outputs, persistence |

`AV(x)` and `RV(x)` remain contract-checker classifications. A profile can block, allow, sandbox, or log an event, but only the contract checker determines whether that event is attempted overreach or a realized contract violation.
