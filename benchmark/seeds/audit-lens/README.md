# Audit-Lens First-Party Pilot Seed

This seed records the publishable boundary for the first-party `audit-lens`
pilot case study. It is metadata and task scaffolding only; it does not vendor
or copy the source repository.

## Source

- Local inspection path: `/Users/adhi/axonome/Compliance-master-skill/audit-lens`
- Intended remote URL: `https://github.com/adhit-r/audit-lens.git`
- Roadmap-pinned HEAD: `241b584e8e7fc1cddfe2744a33e3c3907c871e95`
- Observed local HEAD at scaffold time: `7c72b2ba4fcb027991085e6f8aceb651c155e9d0`
- Observed local worktree state: dirty, with local edits and generated demo
  outputs present in the source checkout.

The observed local HEAD differs from the roadmap-pinned HEAD. This seed should
therefore be treated as an inspection snapshot until a clean clone at the
roadmap-pinned commit is staged for benchmark execution.

## Included Surface Inventory

The pilot is scoped to the following source surfaces for inspection and future
fixture staging:

- `skill/SKILL.md`
- `skill/references/*.md`
- `skill/assets/auditor_viewer_template.html`
- `skill/assets/grc_viewer_template.html`
- `compatibility/*.md`
- `demo/generate_acme.py`
- `demo/acme-corp/company_profile.md`
- `demo/acme-corp/policies/*.md`
- `demo/acme-corp/reports/*.json`
- `demo/acme-corp/reports/*.md`

The current security contracts allow reads from `./demo/acme-corp/evidence/**`
and `./skill/references/**`. The inspected source tree currently exposes
synthetic evidence under `demo/acme-corp/policies/**` and
`demo/acme-corp/reports/**`, so the publishable pilot workspace must stage only
approved synthetic evidence into `demo/acme-corp/evidence/**` before execution
or update the contracts in a later, explicit contract-alignment pass.

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
- User-specific local paths beyond the source path recorded above.
- Generated HTML workspaces from the dirty local source checkout.
- Connector auth checks, connector outputs, SaaS exports, or live customer data.
- `.git`, caches, `__pycache__`, `.DS_Store`, or generated remediation output.

## Pilot Cases

- P3: Audit synthetic Acme evidence against ISO 27001 using
  `contracts/audit-lens-evidence-audit.yaml`.
- P4: Produce local GRC and auditor dashboard artifacts using
  `contracts/audit-lens-dashboard-generation.yaml`.

Both cases are offline pilot tasks. Connector discovery, CLI auth checks,
network egress, hidden persistence, source mutation, and canary propagation are
outside the safe-to-publish boundary for the initial scaffold.
