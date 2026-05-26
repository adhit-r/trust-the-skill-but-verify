# docs-forge Live RP3 Node Adversarial npx Package-Acquisition Result

This artifact records a bounded Dockerized adversarial package-name npx
probe for the pinned docs-forge source boundary. The command points npm
at a controlled loopback registry endpoint inside a Node-capable
RP3-derived container and expects fail-closed behavior before public
registry acquisition, install behavior, lifecycle scripts, or
docs-forge help execution can complete.

| Case | npx Exit | Image | Registry | Fail Closed | Source Mutations | Home Mutations | Result |
| --- | ---: | --- | --- | --- | ---: | ---: | --- |
| rp3_node_package_name_npx_loopback_registry_fail_closed | 1 | `sha256:2ad42c75739973d9bebb233eed1e6e6056c32655a621dd4246d620aba0cef955` | `http://127.0.0.1:9/` | yes | 0 | 0 | passed |

## Container Boundary

- Docker ran with `--network=none` and `--read-only` for the preflight and npx commands.
- The package-name npx attempt did not mount the docs-forge source checkout.
- The command intentionally uses package-name `npx docs-forge --help` under a loopback registry control.
- The observed result is fail-closed: the package was not acquired and docs-forge help did not execute.
- No public npm registry URL, package install command, lifecycle script, source mutation, or home mutation was observed.
- This is adversarial package-acquisition readiness evidence only; it is not public-registry acquisition evidence, packet-capture evidence, or runtime-drift evidence.
