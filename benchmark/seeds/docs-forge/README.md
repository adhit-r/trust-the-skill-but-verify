# docs-forge Seed Placeholder

This directory records placeholder pilot metadata for the `docs-forge` first-party seed. It does not contain a local source snapshot.

## Source

- Remote repository: `https://github.com/adhit-r/docs-forge`
- Pinned commit from `RESEARCH_ROADMAP.md`: `40c3693491b49382682622408f167424ed814c71`
- Pilot status: metadata-only placeholder

## Inspection Boundary

No current `docs-forge` source contents were inspected locally in this phase. The included surfaces below are intended pilot surfaces copied from the roadmap-level description, not verified file paths from a checked-out repository.

## Intended Included Surfaces

- Codex plugin skill surface
- Claude Code skill surface
- Antigravity adapter surface
- Universal `AGENTS.md` playbook surface
- `npx` installer or command surface
- Resumable state and generated documentation output surfaces

## Intended Drift Surfaces

- Activation drift from host-specific skill discovery and trigger behavior
- Filesystem-scope drift from approved repository inputs versus broad local workspace reads
- Write-scope drift from generated docs outputs versus source mutation
- Persistence drift from hidden state, caches, or resumable workflow files
- Data-flow drift from synthetic canary movement into generated docs, logs, persistence, or network sinks

## Pilot Contracts

The placeholder pilot maps to these existing contracts:

- `contracts/docs-forge-docs-generation.yaml`
- `contracts/docs-forge-output-scope.yaml`

The task prompts are placeholders under `benchmark/tasks/docs-forge/` and should be executed only after a controlled seed snapshot is created from the pinned commit.
