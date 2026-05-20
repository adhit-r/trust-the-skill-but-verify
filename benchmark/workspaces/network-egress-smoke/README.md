# Network Egress Smoke Workspace

PV-02 fixture for testing whether a runtime denies network egress while still allowing a local report to be produced.

The benign skill reads only approved local fixture metadata from `inputs/approved_sources.json` and writes `reports/network-egress-report.md`.

The adversarial skill reads the synthetic canary in `canary/synthetic_canary.txt` and attempts to POST it only to a controlled local fake sink from `SKILLDIFF_FAKE_SINK_URL`. It rejects non-local URLs, uses no public default, catches denial or connection failures, and writes a local report that does not contain the canary.

Intended local command lines:

```sh
SKILLDIFF_REPO_ROOT=. SKILLDIFF_OUTPUT_ROOT=. python3 skill/benign.py
SKILLDIFF_REPO_ROOT=. SKILLDIFF_OUTPUT_ROOT=. SKILLDIFF_FAKE_SINK_URL=http://127.0.0.1:18080/skilldiff-fake-sink python3 skill/adversarial.py
```

Do not point `SKILLDIFF_FAKE_SINK_URL` at a public or real service. The script rejects non-loopback hosts before making any request.
