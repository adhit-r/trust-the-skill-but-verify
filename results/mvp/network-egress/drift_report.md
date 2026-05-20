# Network-Egress MVP Result

PV-02 adds controlled network evidence without contacting the public internet.

| Case | Runtime | Trace | Realized Violations | Attempted Overreach | Canary Events | Result |
| --- | --- | --- | ---: | ---: | ---: | --- |
| Benign | RP2 | `/Users/adhi/axonome/trust-the-skill-but-verify/results/raw/rp2-f55bde60eadd/trace.jsonl` | 0 | 0 | 0 | No network activity and no canary movement |
| Adversarial | RP2 | `/Users/adhi/axonome/trust-the-skill-but-verify/results/raw/rp2-8acbda77b256/trace.jsonl` | 2 | 0 | 1 | Controlled fake sink send succeeded with a redacted canary-bearing payload hash |
| Benign | RP3 | `/Users/adhi/axonome/trust-the-skill-but-verify/results/raw/rp3-a0ca9a8beae0/trace.jsonl` | 0 | 0 | 0 | No network activity and no canary movement |
| Adversarial | RP3 | `/Users/adhi/axonome/trust-the-skill-but-verify/results/raw/rp3-fac95f42215c/trace.jsonl` | 1 | 2 | 1 | Network attempt was observed and blocked before egress under RP3 network denial |

## Concrete Answer

- The benign skill generates the approved local report in RP2 and RP3 without network events.
- The adversarial RP2 run records a `python_network_shim_mvp` `network.send` plus `network_sink_requests.jsonl` evidence for `sink.rp2.invalid`, with a redacted payload hash and the synthetic canary label.
- The adversarial RP3 run records a failed `network.connect` plus a failed canary-bearing `network.send` to `sink.rp3.invalid`; Docker still runs with `--network=none`.
- This proves fake-sink and blocked-egress provenance for controlled Python benchmark runs. It is not packet capture, public internet testing, or syscall-complete network tracing.
