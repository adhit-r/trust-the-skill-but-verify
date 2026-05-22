# docs-forge Seed Record

This directory records the first-party `docs-forge` seed provenance for the controlled P1/P2 MVP pilots.

## Source

- Remote repository: `https://github.com/adhit-r/docs-forge`
- Pinned commit: `40c3693491b49382682622408f167424ed814c71`
- Pinned tree: `6fbaec7f16561e5cedd7725d05613ce4a0e61739`
- Local inspection path: `/Users/adhi/Documents/Codex/2026-05-06/files-mentioned-by-the-user-docs`
- Local tracked state at inspection: clean

## Execution Boundary

The benchmark does not vendor the full docs-forge repository and does not execute the real Node installer.
The executable evidence uses `benchmark/workspaces/docs-forge-mini`, a synthetic benchmark-owned fixture that emulates docs-forge-style documentation tasks under the same contract surfaces.

## Verified Included Surfaces

- Codex plugin skill provenance
- Claude Code skill provenance
- Antigravity adapter provenance
- Universal `AGENTS.md` playbook provenance
- Controlled documentation generation workload
- Generated documentation outputs

## Drift Surfaces

- Activation drift from host-specific skill discovery and trigger behavior
- Filesystem-scope drift from approved repository inputs versus broad local workspace reads
- Write-scope drift from generated docs outputs versus source mutation
- Persistence drift from hidden state, caches, or resumable workflow files
- Data-flow drift from synthetic canary movement into generated docs, logs, persistence, or network sinks

## Pilot Contracts

- `contracts/docs-forge-docs-generation.yaml`
- `contracts/docs-forge-output-scope.yaml`

Reproduce the executed P1/P2 fixture with:

```bash
PYTHON_BIN=/private/tmp/skilldiff-venv/bin/python experiments/docs-forge-mvp/reproduce_docs_forge_mvp.sh
```
