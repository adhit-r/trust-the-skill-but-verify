# Artifact README Draft

This is the paper-artifact README draft for the current MVP repository state.
It is intentionally narrower than a final public artifact package.

## Install

Use a clean checkout with Python 3.11+ and Docker available for RP3 runs.

```bash
python3 -m venv /tmp/skilldiff-venv
/tmp/skilldiff-venv/bin/pip install -r requirements-dev.txt
PYTHON_BIN=/tmp/skilldiff-venv/bin/python make verify
```

The existing reproduction scripts also accept `PYTHON_BIN`:

```bash
PYTHON_BIN=/tmp/skilldiff-venv/bin/python bash experiments/repo-audit-mvp/reproduce_repo_audit_mvp.sh
PYTHON_BIN=/tmp/skilldiff-venv/bin/python bash experiments/network-egress-mvp/reproduce_network_egress_mvp.sh
PYTHON_BIN=/tmp/skilldiff-venv/bin/python bash experiments/audit-lens-mvp/reproduce_audit_lens_mvp.sh
PYTHON_BIN=/tmp/skilldiff-venv/bin/python bash experiments/docs-forge-mvp/reproduce_docs_forge_mvp.sh
PYTHON_BIN=/tmp/skilldiff-venv/bin/python bash experiments/first-party-source-provenance/reproduce_first_party_source_provenance.sh
```

If external first-party source checkouts are available, pass them explicitly to
verify pinned provenance before the fixture runs:

```bash
DOCS_FORGE_SOURCE_ROOT=/path/to/docs-forge \
  PYTHON_BIN=/tmp/skilldiff-venv/bin/python \
  bash experiments/docs-forge-mvp/reproduce_docs_forge_mvp.sh

AUDIT_LENS_SOURCE_ROOT=/path/to/audit-lens \
  PYTHON_BIN=/tmp/skilldiff-venv/bin/python \
  bash experiments/audit-lens-mvp/reproduce_audit_lens_mvp.sh
```

The bounded docs-forge live-installer dry-run check also requires the pinned
docs-forge source checkout:

```bash
DOCS_FORGE_SOURCE_ROOT=/path/to/docs-forge \
  PYTHON_BIN=/tmp/skilldiff-venv/bin/python \
  bash experiments/docs-forge-live-installer/reproduce_docs_forge_live_installer.sh
```

The bounded docs-forge project-local non-dry-run installer check also requires
the pinned docs-forge source checkout:

```bash
DOCS_FORGE_SOURCE_ROOT=/path/to/docs-forge \
  PYTHON_BIN=/tmp/skilldiff-venv/bin/python \
  bash experiments/docs-forge-live-project-local-install/reproduce_docs_forge_live_project_local_install.sh
```

The bounded docs-forge live runtime-pair scaffold also requires the pinned
docs-forge source checkout:

```bash
DOCS_FORGE_SOURCE_ROOT=/path/to/docs-forge \
  PYTHON_BIN=/tmp/skilldiff-venv/bin/python \
  bash experiments/docs-forge-live-runtime-pair/reproduce_docs_forge_live_runtime_pair.sh
```

The bounded docs-forge live package-observer check also requires the pinned
docs-forge source checkout:

```bash
DOCS_FORGE_SOURCE_ROOT=/path/to/docs-forge \
  PYTHON_BIN=/tmp/skilldiff-venv/bin/python \
  bash experiments/docs-forge-live-package-observer/reproduce_docs_forge_live_package_observer.sh
```

The bounded docs-forge live local-tarball npx observer also requires the pinned
docs-forge source checkout:

```bash
DOCS_FORGE_SOURCE_ROOT=/path/to/docs-forge \
  PYTHON_BIN=/tmp/skilldiff-venv/bin/python \
  bash experiments/docs-forge-live-npx-observer/reproduce_docs_forge_live_npx_observer.sh
```

The bounded docs-forge RP3 Node local-tarball npx observer additionally
requires the pinned `skilldiff-rp3-node` image or an explicit
`SKILLDIFF_RP3_NODE_IMAGE_REF`:

```bash
docker build --pull=false -t skilldiff-rp3-node:0.1 runtimes/docker/rp3-node
DOCS_FORGE_SOURCE_ROOT=/path/to/docs-forge \
  SKILLDIFF_RP3_NODE_IMAGE_REF=sha256:2ad42c75739973d9bebb233eed1e6e6056c32655a621dd4246d620aba0cef955 \
  PYTHON_BIN=/tmp/skilldiff-venv/bin/python \
  bash experiments/docs-forge-live-npx-rp3-node-observer/reproduce_docs_forge_live_npx_rp3_node_observer.sh
```

The bounded docs-forge live npx runtime-pair scaffold also requires the pinned
docs-forge source checkout and RP3 Node image:

```bash
DOCS_FORGE_SOURCE_ROOT=/path/to/docs-forge \
  SKILLDIFF_RP3_NODE_IMAGE_REF=sha256:2ad42c75739973d9bebb233eed1e6e6056c32655a621dd4246d620aba0cef955 \
  PYTHON_BIN=/tmp/skilldiff-venv/bin/python \
  bash experiments/docs-forge-live-npx-runtime-pair/reproduce_docs_forge_live_npx_runtime_pair.sh
```

The bounded docs-forge adversarial package-name npx observer also requires the
pinned docs-forge source checkout:

```bash
DOCS_FORGE_SOURCE_ROOT=/path/to/docs-forge \
  PYTHON_BIN=/tmp/skilldiff-venv/bin/python \
  bash experiments/docs-forge-live-npx-adversarial-package-acquisition/reproduce_docs_forge_live_npx_adversarial_package_acquisition.sh
```

The bounded docs-forge RP3 Node adversarial package-name npx observer also
requires the pinned docs-forge source checkout and RP3 Node image:

```bash
DOCS_FORGE_SOURCE_ROOT=/path/to/docs-forge \
  SKILLDIFF_RP3_NODE_IMAGE_REF=sha256:2ad42c75739973d9bebb233eed1e6e6056c32655a621dd4246d620aba0cef955 \
  PYTHON_BIN=/tmp/skilldiff-venv/bin/python \
  bash experiments/docs-forge-live-npx-rp3-node-adversarial-package-acquisition/reproduce_docs_forge_live_npx_rp3_node_adversarial_package_acquisition.sh
```

The bounded docs-forge adversarial npx runtime-pair scaffold also requires the
pinned docs-forge source checkout and RP3 Node image:

```bash
DOCS_FORGE_SOURCE_ROOT=/path/to/docs-forge \
  SKILLDIFF_RP3_NODE_IMAGE_REF=sha256:2ad42c75739973d9bebb233eed1e6e6056c32655a621dd4246d620aba0cef955 \
  PYTHON_BIN=/tmp/skilldiff-venv/bin/python \
  bash experiments/docs-forge-live-npx-adversarial-package-acquisition-runtime-pair/reproduce_docs_forge_live_npx_adversarial_package_acquisition_runtime_pair.sh
```

The bounded RP4 MCP-connected fixture is local and synthetic. It does not
require an external MCP server, connector credentials, Docker, or public
network access:

```bash
PYTHON_BIN=/tmp/skilldiff-venv/bin/python \
  bash experiments/rp4-mcp-connected-mvp/reproduce_rp4_mcp_connected_mvp.sh
```

The RP6 current-case report card is also local and synthetic. It reruns the
existing fourteen case variants under the policy-hardened adapter and keeps the
results outside RP2/RP3 MVP aggregate counts. It also runs one supplemental
network-denial policy probe inside the fixture results directory:

```bash
PYTHON_BIN=/tmp/skilldiff-venv/bin/python \
  bash experiments/rp6-policy-hardened-mvp/reproduce_rp6_policy_hardened_mvp.sh
```

The strengthening evidence package builds static and derived baseline artifacts
from existing results, runs generated RP6 component-ablation profiles, then
runs RP6 repeat IDs 2 and 3 to produce a bounded three-repeat deterministic
stability check:

```bash
PYTHON_BIN=/tmp/skilldiff-venv/bin/python \
  bash experiments/strengthening-evidence/reproduce_strengthening_evidence.sh
```

## Expected Outputs

| Script | Primary Result |
| --- | --- |
| `experiments/repo-audit-mvp/reproduce_repo_audit_mvp.sh` | `results/mvp/repo-audit/drift_report.md` |
| `experiments/network-egress-mvp/reproduce_network_egress_mvp.sh` | `results/mvp/network-egress/drift_report.md` |
| `experiments/audit-lens-mvp/reproduce_audit_lens_mvp.sh` | `results/mvp/audit-lens/drift_report.md` |
| `experiments/docs-forge-mvp/reproduce_docs_forge_mvp.sh` | `results/mvp/docs-forge/drift_report.md` |
| `experiments/first-party-source-provenance/reproduce_first_party_source_provenance.sh` | `results/external/first-party-source-provenance.md` |
| `experiments/docs-forge-live-installer/reproduce_docs_forge_live_installer.sh` | `results/live/docs-forge-installer/dry_run_report.md` |
| `experiments/docs-forge-live-project-local-install/reproduce_docs_forge_live_project_local_install.sh` | `results/live/docs-forge-installer/project_local_install_report.md` |
| `experiments/docs-forge-live-runtime-pair/reproduce_docs_forge_live_runtime_pair.sh` | `results/live/docs-forge-installer/project_local_runtime_pair_report.md` |
| `experiments/docs-forge-live-package-observer/reproduce_docs_forge_live_package_observer.sh` | `results/live/docs-forge-installer/package_observer_report.md` |
| `experiments/docs-forge-live-npx-observer/reproduce_docs_forge_live_npx_observer.sh` | `results/live/docs-forge-installer/npx_observer_report.md` |
| `experiments/docs-forge-live-npx-rp3-node-observer/reproduce_docs_forge_live_npx_rp3_node_observer.sh` | `results/live/docs-forge-installer/npx_rp3_node_observer_report.md` |
| `experiments/docs-forge-live-npx-runtime-pair/reproduce_docs_forge_live_npx_runtime_pair.sh` | `results/live/docs-forge-installer/npx_runtime_pair_report.md` |
| `experiments/docs-forge-live-npx-adversarial-package-acquisition/reproduce_docs_forge_live_npx_adversarial_package_acquisition.sh` | `results/live/docs-forge-installer/npx_adversarial_package_acquisition_report.md` |
| `experiments/docs-forge-live-npx-rp3-node-adversarial-package-acquisition/reproduce_docs_forge_live_npx_rp3_node_adversarial_package_acquisition.sh` | `results/live/docs-forge-installer/npx_rp3_node_adversarial_package_acquisition_report.md` |
| `experiments/docs-forge-live-npx-adversarial-package-acquisition-runtime-pair/reproduce_docs_forge_live_npx_adversarial_package_acquisition_runtime_pair.sh` | `results/live/docs-forge-installer/npx_adversarial_package_acquisition_runtime_pair_report.md` |
| `experiments/rp4-mcp-connected-mvp/reproduce_rp4_mcp_connected_mvp.sh` | `results/fixtures/rp4-mcp-connected/drift_report.md` |
| `experiments/rp6-policy-hardened-mvp/reproduce_rp6_policy_hardened_mvp.sh` | `results/fixtures/rp6-policy-hardened/report_card.json` plus `results/fixtures/rp6-policy-hardened/network-egress/network_policy_probe_rp6_contract_findings.json` |
| `experiments/strengthening-evidence/reproduce_strengthening_evidence.sh` | `results/fixtures/strengthening/index.json` plus `results/fixtures/rp6-policy-hardened/ablations/component_report_card.json` and `results/fixtures/rp6-policy-hardened/ablations/minimal_report_card.json` |

## Safety Notes

- The repository uses synthetic canaries only.
- Benchmark network tests use reserved fake-sink destinations or Docker network
  denial; they must not contact the public internet.
- Raw payload bodies, raw query strings, sensitive headers, and real secrets are
  outside the artifact boundary.
- Local machine paths are scrubbed to placeholders such as `<REPO_ROOT>` and
  `<LOCAL_SOURCE_CHECKOUT:docs-forge>`.
- Reproduction scripts scrub generated raw traces and MVP result files after
  local validation so checked-in artifacts remain publishable.
- First-party seed repos are referenced by commit hash; full source trees are
  not vendored into the publishable fixture. Published source hash lists cover
  11 docs-forge source entries and 42 AuditLens source entries.
- `results/external/first-party-source-provenance.json` records clean
  ephemeral-clone verification for those pinned first-party source hashes
  without vendoring the source trees or executing full products.
- `results/live/docs-forge-installer/dry_run_result.json` records bounded
  Node CLI help, version, and installer dry-run evidence against a disposable
  target. It is excluded from MVP runtime-drift counts.
- `results/live/docs-forge-installer/project_local_install_result.json`
  records one bounded project-local non-dry-run installer command against a
  disposable target. It allows only expected project-local skill/playbook
  writes and is excluded from MVP runtime-drift counts.
- `results/live/docs-forge-installer/project_local_runtime_pair_result.json`
  records two bounded project-local installer commands across host-environment
  and minimal-environment synthetic-home Node executions. It compares target
  mutation hashes and output hashes, and is excluded from MVP runtime-drift
  counts.
- `results/live/docs-forge-installer/package_observer_result.json` records one
  bounded offline local `npm pack --ignore-scripts` package materialization
  into an ephemeral package directory. It records tarball and expected package
  entry evidence, and is excluded from MVP runtime-drift counts.
- `results/live/docs-forge-installer/npx_observer_result.json` records one
  bounded local-tarball `npx --offline` help execution from the locally
  materialized docs-forge package. It does not execute package-name `npx`, npm
  registry acquisition, install behavior, or docs generation.
- `results/live/docs-forge-installer/npx_rp3_node_observer_result.json`
  records one containerized local-tarball `npx --offline` help execution under
  Docker `--network=none` and `--read-only` constraints. It does not execute
  package-name `npx`, npm registry acquisition, install behavior, or docs
  generation, and it remains excluded from MVP runtime-drift counts.
- `results/live/docs-forge-installer/npx_runtime_pair_result.json` records a
  bounded comparison between the host Node synthetic-home npx observer and the
  RP3 Node container npx observer. Required pair checks pass, informational
  Node/npm/cache/tarball differences are not treated as drift, and the result
  remains excluded from MVP runtime-drift counts.
- `results/live/docs-forge-installer/npx_adversarial_package_acquisition_result.json`
  records one bounded package-name `npx docs-forge --help` probe against a
  controlled loopback registry. It observes fail-closed behavior and remains
  excluded from MVP runtime-drift counts.
- `results/live/docs-forge-installer/npx_rp3_node_adversarial_package_acquisition_result.json`
  records one bounded package-name `npx docs-forge --help` probe against a
  controlled nonpublic registry target inside a Node-capable RP3-derived
  container. It observes fail-closed behavior under Docker network denial and
  read-only root filesystem constraints, and remains excluded from MVP
  runtime-drift counts.
- `results/live/docs-forge-installer/npx_adversarial_package_acquisition_runtime_pair_result.json`
  records a bounded comparison between the host Node synthetic-home
  adversarial package-name npx observer and the RP3 Node container adversarial
  observer. Required pair checks pass, exact nonzero exit-code equality is
  informational, and the result remains excluded from MVP runtime-drift counts.

## Known Limitations

- RP2 read provenance is Python wrapper-level.
- Failed Python write-attempt provenance is wrapper-level evidence for
  controlled Python commands.
- RP3 file-read provenance is container-strace MVP coverage for supported
  `open`, `openat`, and `openat2` events.
- The current artifact measures approval, MCP-style tool-call, and persistence
  surfaces through controlled semantic-event fixtures, including the bounded
  RP4 local MCP fixture. It does not measure external MCP server behavior,
  connector auth, commercial MCP-client behavior, or complete persistence
  behavior.
- RP6 is a current-case mitigation report-card pilot with wrapper-level
  controlled Python enforcement and controlled semantic-fixture tool
  normalization. Its supplemental network policy probe exercises blocked
  fake-sink connect/send events, but RP6 remains not syscall-complete hardening,
  not RP6-vs-RP2/RP3 runtime-drift evidence, and not a defense-success claim.
- Strengthening artifacts add a contract-derived least-privilege budget, coarse
  mitigation ladder, minimal RP6 contrast, bounded RP6 component-ablation
  fixture evidence across six controls, and bounded deterministic RP6 repeat
  stability across repeat IDs 1, 2, and 3. They do not prove product-scale
  defense causality or statistical/model-mediated repeat stability.
- docs-forge P1/P2 runtime-drift evidence is represented by a controlled Python
  docs-forge-style fixture. The live-installer evidence covers dry-run and
  project-local installer-only execution; it is not docs generation, user/global
  installation, or `npx` execution.
- AuditLens is represented by a sanitized synthetic Acme fixture, not full
  product or connector execution.
- First-party source provenance is source-only evidence; it does not create
  new runtime-drift claims by itself.
- docs-forge live-installer evidence does not prove network absence under
  packet capture or complete Node runtime tracing.
- docs-forge live runtime-pair evidence is a local Node environment-pair
  scaffold. It is not RP2/RP3 runtime-drift evidence, `npx`
  package-acquisition evidence, or full docs-generation evidence.
- docs-forge live package-observer evidence is offline local package
  materialization. It is not `npx` execution, npm registry acquisition,
  package-install behavior, public-internet packet-capture evidence, or
  runtime-drift evidence.
- docs-forge live local-tarball npx evidence is offline local-tarball help
  execution. It is not public registry acquisition, package-name
  `npx docs-forge`, package-install behavior, public-internet packet-capture
  evidence, or runtime-drift evidence.
- docs-forge live RP3 Node local-tarball npx evidence is RP3-containerized
  help execution under Docker network denial. It is not packet capture,
  public-registry package acquisition, package-name `npx docs-forge`,
  package-install behavior, docs generation, or RP2/RP3 drift evidence.
- docs-forge live npx runtime-pair evidence is a scaffold comparing benign
  local-tarball help behavior only. It is not an adversarial npx/package
  acquisition study, public-registry evidence, packet-capture evidence, or
  runtime-drift evidence.
- docs-forge adversarial package-name npx evidence is a fail-closed loopback
  registry probe. It is not successful package acquisition, public-registry
  evidence, package-install behavior, lifecycle-script execution,
  packet-capture evidence, docs generation, or runtime-drift evidence.
- docs-forge RP3 Node adversarial package-name npx evidence is a fail-closed
  controlled nonpublic registry probe inside a Docker network-denied container.
  It is not public-registry evidence, packet-capture evidence, successful
  package acquisition, package-install behavior, lifecycle-script execution,
  docs generation, or runtime-drift evidence.
- docs-forge adversarial npx runtime-pair evidence compares fail-closed safety
  invariants only. It is not public npm acquisition evidence, packet-capture
  coverage, successful install behavior, or an added runtime-drift finding.

## Release Checklist

- [x] Replace local filesystem paths with publishable placeholders.
- [x] Keep real secrets out of fixtures and results.
- [x] Keep public internet contact out of benchmark runs.
- [x] Preserve synthetic canary labels for reproducible detection.
- [x] Maintain a validated paper claim ledger.
- [x] Complete published pinned-source hash lists for first-party seed repos.
- [ ] Add a top-level `SECURITY.md`.
- [ ] Add final license and citation metadata.
