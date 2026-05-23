# docs-forge Live Project-Local Install Result

This artifact records bounded live Node CLI evidence for the pinned
docs-forge source checkout. It executes one non-dry-run project-local
installer command against a disposable synthetic target.

| Case | Exit | Expected Target Writes | Unexpected Target Writes | Source Mutations | Home Mutations | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| project_local_install | 0 | 3 | 0 | 0 | 0 | passed |

## Expected Target Writes

- `.claude/skills/docs-forge/SKILL.md`
- `AGENTS.md`
- `GEMINI.md`

## Boundary

- This is project-local installer evidence, not docs-generation evidence.
- It is excluded from MVP runtime-drift counts.
- It does not run `npx`, install packages, modify user home directories, or execute the Codex marketplace command.
- It uses Node filesystem-call instrumentation and source/target/home pre/post checks, but it is not packet capture or complete Node runtime tracing.
