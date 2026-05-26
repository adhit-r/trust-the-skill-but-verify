# Security Policy

## Artifact Boundary

SkillDiff benchmark artifacts are designed for controlled research use. The
publishable artifact uses synthetic fixtures, synthetic canaries, local fake
sinks, and bounded runtime profiles. It does not require real credentials,
cookies, live SaaS exports, auth state, or public-network exfiltration.

## Synthetic Canary Policy

Synthetic canaries are intentionally placed in benchmark workspaces to test
whether runtime traces and contract checks detect unauthorized reads,
propagation, persistence, logging, tool messages, or network sends. Canary
values are not real secrets. Reports must describe only synthetic canary
movement and must not imply real-credential theft.

## Public Network Policy

Experiments must not contact public exfiltration endpoints. Network evidence
uses reserved fake-sink destinations, loopback registry probes, Docker network
denial, or explicitly bounded local fixtures. Any future public-network
experiment requires a new safety review, a tracked protocol, and claim-ledger
coverage before it can be paper-facing.

## Reporting Security Issues

Report suspected leaks, unsafe experiment definitions, real credential
exposure, or publishability issues through the repository's private issue or
maintainer contact path. Do not include real secrets in reports. Include the
affected file path, command, and a minimal reproduction using synthetic data.

## Non-Claims

Current artifacts do not claim commercial-runtime behavior, real connector
authorization behavior, public-internet exfiltration, syscall-complete tracing,
ecosystem prevalence, or product-scale defense success.
