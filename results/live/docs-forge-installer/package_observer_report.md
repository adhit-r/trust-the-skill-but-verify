# docs-forge Live Package Observer Result

This artifact records bounded offline npm package-observer evidence for
the pinned docs-forge source checkout. It materializes the local package
with lifecycle scripts disabled and does not execute `npx`, install from
a registry, or run docs generation.

| Case | Exit | Package | Entries | Source Mutations | Home Mutations | Result |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| local_npm_pack_observer | 0 | docs-forge@0.3.0 | 10 | 0 | 0 | passed |

## Observed Package Files

- `LICENSE`
- `README.md`
- `adapters/antigravity/AGENTS.md`
- `adapters/antigravity/GEMINI.md`
- `adapters/claude-code/README.md`
- `adapters/universal/AGENTS.md`
- `bin/docs-forge.js`
- `package.json`
- `plugins/docs-forge/.codex-plugin/plugin.json`
- `plugins/docs-forge/skills/docs-forge/SKILL.md`

## Boundary

- This is offline local `npm pack` evidence, not `npx` execution or registry acquisition evidence.
- It is excluded from MVP runtime-drift counts.
- It disables npm lifecycle scripts and uses synthetic HOME plus an ephemeral npm cache.
- It does not prove public-internet safety under packet capture or complete Node/npm runtime tracing.
