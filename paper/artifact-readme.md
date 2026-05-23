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

## Known Limitations

- RP2 read provenance is Python wrapper-level.
- Failed Python write-attempt provenance is wrapper-level evidence for
  controlled Python commands.
- RP3 file-read provenance is container-strace MVP coverage for supported
  `open`, `openat`, and `openat2` events.
- The current artifact measures approval, MCP-style tool-call, and persistence
  surfaces only through a controlled semantic-event fixture. It does not
  measure live MCP server behavior, connector auth, or complete persistence
  behavior.
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

## Release Checklist

- [x] Replace local filesystem paths with publishable placeholders.
- [x] Keep real secrets out of fixtures and results.
- [x] Keep public internet contact out of benchmark runs.
- [x] Preserve synthetic canary labels for reproducible detection.
- [x] Maintain a validated paper claim ledger.
- [x] Complete published pinned-source hash lists for first-party seed repos.
- [ ] Add a top-level `SECURITY.md`.
- [ ] Add final license and citation metadata.
