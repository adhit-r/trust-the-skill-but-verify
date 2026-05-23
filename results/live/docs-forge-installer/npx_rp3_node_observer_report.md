# docs-forge Live RP3 Node Local-Tarball npx Observer Result

This artifact records bounded Dockerized npx evidence for the pinned
docs-forge source checkout. It uses an experimental Node-capable RP3
image with Docker networking disabled, materializes one local tarball
with lifecycle scripts disabled, then runs docs-forge help through
`npx --offline` from that local tarball.

| Case | npx Exit | Image | Package | Entries | Source Mutations | Home Mutations | Result |
| --- | ---: | --- | --- | ---: | ---: | ---: | --- |
| rp3_node_local_tarball_npx_help | 0 | `sha256:2ad42c75739973d9bebb233eed1e6e6056c32655a621dd4246d620aba0cef955` | docs-forge@0.3.0 | 10 | 0 | 0 | passed |

## Container Boundary

- Docker ran with `--network=none` and `--read-only` for the preflight, package, and npx commands.
- The docs-forge source checkout was mounted read-only for package materialization.
- `npx` used `--offline` and `--package /workspace/package/docs-forge-0.3.0.tgz`.
- No package-name `npx docs-forge` registry acquisition was executed.
- No package install command, lifecycle script, docs generation, or project/user/global installer write was executed.
- This is not an MVP RP2/RP3 runtime-drift claim.
