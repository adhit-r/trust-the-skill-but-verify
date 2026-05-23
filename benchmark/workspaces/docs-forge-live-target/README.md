# docs-forge Live Installer Target

Disposable target fixture for live docs-forge installer dry-run checks.

The runner copies this directory to a temporary workspace before invoking the
real docs-forge Node CLI from an external pinned source checkout. Checked-in
files here are synthetic and safe to publish.
