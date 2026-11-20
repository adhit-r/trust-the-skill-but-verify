# Collection notes

Requests live in one folder per API area; `seq` sets the run order inside a folder.

- Base URLs and sample identifiers come from the files in `environments/`.
- Secrets such as `accessToken` are declared under `vars:secret` and filled in per developer, never committed.
- Every request that returns data should assert at least the status code and one body field.
- `idempotencyKey` and `orderStatus` are set by the pre-request scripts of the runner, not by an environment file.
