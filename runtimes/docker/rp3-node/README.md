# RP3 Node Docker Image

This directory owns an experimental Node/npm extension of the pinned RP3 image.
It is used only for bounded docs-forge local-tarball `npx` probes and is not
part of the MVP RP2/RP3 runtime-drift baseline.

The current recorded image ref is:

```bash
sha256:2ad42c75739973d9bebb233eed1e6e6056c32655a621dd4246d620aba0cef955
```

Build locally:

```bash
docker build --pull=false -t skilldiff-rp3-node:0.1 runtimes/docker/rp3-node
```

Inspect the resulting immutable image ID:

```bash
docker image inspect skilldiff-rp3-node:0.1 --format '{{.Id}}'
```

If the ID changes because Debian package metadata changed, refresh the
corresponding manifest, result, and claim-ledger evidence before treating the
new run as publishable.
