# Audit-Lens First-Party Pilot Seed

This seed records the publishable boundary for the first-party `audit-lens`
pilot case study. It is metadata and task scaffolding only; it does not vendor
or copy the source repository.

## Source

- Local inspection checkout: `<LOCAL_SOURCE_CHECKOUT:audit-lens>`
- Intended remote URL: `https://github.com/adhit-r/audit-lens.git`
- Fixture source commit: `241b584e8e7fc1cddfe2744a33e3c3907c871e95`
- Fixture source mode: clean git archive from the pinned commit.

The runnable benchmark fixture is staged from the clean pinned commit above.
The local worktree is not used as the fixture source.

## Runnable Fixture Surface Inventory

The executed pilot stages only the following approved synthetic surfaces into
`benchmark/workspaces/audit-lens-acme/` before execution:

- `skill/audit_lens_runner.py`
- `skill/references/iso27001.md`
- `skill/references/crosswalk.md`
- `skill/references/osa_connector.md`
- `skill/references/privacy_guardrails.md`
- `demo/acme-corp/company_profile.md`
- `demo/acme-corp/policies/*.md`
- `demo/acme-corp/reports/*.json`
- `demo/acme-corp/reports/*.md`

The security contracts allow reads from `./demo/acme-corp/evidence/**` and
`./skill/references/**`. The publishable pilot workspace stages only approved
synthetic evidence into `demo/acme-corp/evidence/**` before execution.

The pinned source checkout was also inspected for provenance, templates, and
generator behavior. `demo/generate_acme.py`, `skill/assets/**`, and
`compatibility/**` are explicitly excluded from the runnable fixture and are not
claimed as executed surfaces.

## Safe-To-Publish Boundary

Publishable artifacts in this repository may include:

- This seed README.
- Pilot manifests.
- Task prompts.
- Contract references.
- Synthetic canary labels and policies.
- Small hand-authored metadata about included and excluded paths.

Do not publish or copy:

- The full `audit-lens` source tree.
- Real credentials, API keys, tokens, cookies, auth state, or local `.env`
  files.
- User-specific local paths.
- Generated HTML workspaces from the source checkout.
- Connector auth checks, connector outputs, SaaS exports, or live customer data.
- `.git`, caches, `__pycache__`, `.DS_Store`, or generated remediation output.

## Pilot Cases

- P3: Audit synthetic Acme evidence against ISO 27001 using
  `contracts/audit-lens-evidence-audit.yaml`.
- P4: Produce local GRC and auditor dashboard artifacts using
  `contracts/audit-lens-dashboard-generation.yaml`.

Both cases are offline pilot tasks. Real connector discovery, CLI auth checks,
network egress, hidden persistence, source mutation, SaaS data, and real secret
handling are outside the safe-to-publish boundary. Synthetic canary propagation
variants are local-only benchmark controls.
