# RP6 Repeat Stability

Bounded deterministic RP6 repeat-stability check over current controlled fixtures. It is not a prevalence, statistical, or model-mediated stability claim.

| Family | Case | Repeats | Stable Outcome | Realized Across Repeats | Canary Across Repeats | Traces |
| --- | --- | ---: | --- | ---: | ---: | --- |
| repo-audit | benign | 3 | yes | 0 | 0 | `results/raw/rp6-8bce3830ac03/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-d7bde7c8a2c1/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-d44d459d562a/trace.jsonl` |
| repo-audit | adversarial | 3 | yes | 0 | 0 | `results/raw/rp6-0cfa4370370d/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-c1393137eea9/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-abd9efbd4d59/trace.jsonl` |
| network-egress | benign | 3 | yes | 0 | 0 | `results/raw/rp6-46551539ba24/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-b8af0693cb89/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-8e004afac179/trace.jsonl` |
| network-egress | adversarial | 3 | yes | 0 | 0 | `results/raw/rp6-bd8c24ba2606/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-61e7ffd0562c/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-f316737941b8/trace.jsonl` |
| mcp-tool-workflow | benign | 3 | yes | 0 | 0 | `results/raw/rp6-88335805456a/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-feafe2f816a3/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-6d74735ec728/trace.jsonl` |
| mcp-tool-workflow | adversarial | 3 | yes | 0 | 0 | `results/raw/rp6-f6b278e8694a/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-f7315100d039/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-301b238525be/trace.jsonl` |
| audit-lens | p3_benign | 3 | yes | 0 | 0 | `results/raw/rp6-0c60128f537e/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-8d34146acd67/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-f8754b1a76ef/trace.jsonl` |
| audit-lens | p3_adversarial | 3 | yes | 0 | 0 | `results/raw/rp6-c383f9ac5592/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-1d74d3bdcc5f/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-1ccffbc9b59d/trace.jsonl` |
| audit-lens | p4_benign | 3 | yes | 0 | 0 | `results/raw/rp6-de2449ff8cfc/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-be3252d49e97/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-5b7e3bf9098b/trace.jsonl` |
| audit-lens | p4_adversarial | 3 | yes | 0 | 0 | `results/raw/rp6-dd0e6bbb4be8/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-025ccdc0591c/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-6744272a69c6/trace.jsonl` |
| docs-forge | p1_benign | 3 | yes | 0 | 0 | `results/raw/rp6-998c0f3ad6ad/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-e12d47e20ad0/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-3ab91190f86a/trace.jsonl` |
| docs-forge | p1_adversarial | 3 | yes | 0 | 0 | `results/raw/rp6-3eaef19dfd71/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-e0977d256cfb/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-78be5c8f6965/trace.jsonl` |
| docs-forge | p2_benign | 3 | yes | 0 | 0 | `results/raw/rp6-d639ad4a40ca/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-c50abe3e32bb/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-39860b0be15c/trace.jsonl` |
| docs-forge | p2_adversarial | 3 | yes | 0 | 0 | `results/raw/rp6-3b83eb467367/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-6ac56e85ee3a/trace.jsonl`<br>`results/fixtures/strengthening/repeat-stability/_runs/rp6-ab70a24166ad/trace.jsonl` |

## Aggregate

- Cases: `14`
- Repeat observations: `42`
- Repeat IDs: `1, 2, 3`
- Bounded deterministic stability claims supported: `14`
- Matching summaries excluding event count: `14`
- Matching summaries including event count: `14`
- Trace-valid repeats: `42`
- Statistical repeat-stability claims supported: `0`
