# RP3 Docker Image

This directory owns the neutral RP3 Docker image used by `runtimes/profiles/RP3_docker_sandbox.yaml`.

The image is intentionally small and project-neutral:

- It is named `skilldiff-rp3`.
- It contains Python for RP3 live smoke execution.
- It does not copy repository source, benchmark fixtures, credentials, or application code into the image.
- RP3 still enforces network denial, read-only rootfs, explicit mounts, synthetic credentials, and deterministic cleanup through the runtime profile and adapter invocation.

Build locally:

```sh
docker build --pull=false -t skilldiff-rp3:0.1 runtimes/docker/rp3
```

If the pinned `python:3.12.10-slim-bookworm` base digest is not already local, Docker may need network access to pull it. For offline artifact builds, preload that base image or override `PYTHON_BASE_IMAGE` with an equivalent local Python 3.12 slim base:

```sh
docker build --pull=false \
  --build-arg PYTHON_BASE_IMAGE=<local-python-base> \
  -t skilldiff-rp3:0.1 \
  runtimes/docker/rp3
```

Pin the built image by immutable local image ID:

```sh
docker image inspect skilldiff-rp3:0.1 --format '{{.Id}}'
```

Use the returned `sha256:...` value for both `adapter.runtime_constraints.container_image_ref` and `reproducibility.base_image_digest`, then refresh `reproducibility.profile_hash` with:

```sh
python3 tools/validate_runtime_profiles.py --no-hash-check --print-hashes runtimes/profiles/RP3_docker_sandbox.yaml
```
