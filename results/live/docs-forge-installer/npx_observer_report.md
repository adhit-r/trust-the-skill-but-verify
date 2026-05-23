# docs-forge Live Local-Tarball npx Observer Result

This artifact records bounded npx evidence for the pinned docs-forge
source checkout. It first materializes a local tarball with lifecycle
scripts disabled, then runs docs-forge help through `npx --offline` from
that local tarball.

| Case | npx Exit | Package | Entries | Source Mutations | Home Mutations | Result |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| local_tarball_npx_help | 0 | docs-forge@0.3.0 | 10 | 0 | 0 | passed |

## npx Boundary

- `npx` used `--offline` and `--package <local tarball>`.
- The command executed `docs-forge --help` only.
- No package-name `npx docs-forge` registry acquisition was executed.
- No package install command, lifecycle script, docs generation, or project/user/global installer write was executed.
