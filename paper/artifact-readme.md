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

## Expected Outputs

| Script | Primary Result |
| --- | --- |
| `experiments/repo-audit-mvp/reproduce_repo_audit_mvp.sh` | `results/mvp/repo-audit/drift_report.md` |
| `experiments/network-egress-mvp/reproduce_network_egress_mvp.sh` | `results/mvp/network-egress/drift_report.md` |
| `experiments/audit-lens-mvp/reproduce_audit_lens_mvp.sh` | `results/mvp/audit-lens/drift_report.md` |
| `experiments/docs-forge-mvp/reproduce_docs_forge_mvp.sh` | `results/mvp/docs-forge/drift_report.md` |

## Safety Notes

- The repository uses synthetic canaries only.
- Benchmark network tests use reserved fake-sink destinations or Docker network
  denial; they must not contact the public internet.
- Raw payload bodies, raw query strings, sensitive headers, and real secrets are
  outside the artifact boundary.
- Local machine paths are scrubbed to placeholders such as `<REPO_ROOT>` and
  `<LOCAL_SOURCE_CHECKOUT:docs-forge>`.
- First-party seed repos are referenced by commit hash; full source trees are
  not vendored into the publishable fixture.

## Known Limitations

- RP2 read provenance is Python wrapper-level.
- Failed Python write-attempt provenance is wrapper-level evidence for
  controlled Python commands.
- RP3 file-read provenance is container-strace MVP coverage for supported
  `open`, `openat`, and `openat2` events.
- The current artifact does not measure approval prompts, MCP tool calls,
  connector auth, or complete persistence behavior.
- docs-forge is represented by a controlled Python docs-forge-style fixture,
  not by real Node installer execution.
- AuditLens is represented by a sanitized synthetic Acme fixture, not full
  product or connector execution.

## Release Checklist

- [x] Replace local filesystem paths with publishable placeholders.
- [x] Keep real secrets out of fixtures and results.
- [x] Keep public internet contact out of benchmark runs.
- [x] Preserve synthetic canary labels for reproducible detection.
- [~] Add source-provenance hash verification to every reproduction script.
- [ ] Add a top-level `SECURITY.md`.
- [ ] Add final license and citation metadata.
