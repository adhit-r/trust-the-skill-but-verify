# MCP/Tool Workflow MVP Result

P2 adds controlled semantic evidence for activation, approval, tool-call, and persistence surfaces.

| Case | Runtime | Trace | Realized Violations | Attempted Overreach | Canary Events | Result |
| --- | --- | --- | ---: | ---: | ---: | --- |
| Benign | RP2 | `<REPO_ROOT>/results/raw/rp2-787b76ef0fd8/trace.jsonl` | 0 | 0 | 0 | Approved lookup/resource calls with explicit lookup approval and no canary movement |
| Adversarial | RP2 | `<REPO_ROOT>/results/raw/rp2-e3c7ad103873/trace.jsonl` | 7 | 0 | 4 | Denied tool calls and hidden persistence were realized by the scripted RP2 semantic fixture |
| Benign | RP3 | `<REPO_ROOT>/results/raw/rp3-8d57b476932a/trace.jsonl` | 0 | 0 | 0 | Approved lookup/resource calls with the same canonical trace shape under container execution |
| Adversarial | RP3 | `<REPO_ROOT>/results/raw/rp3-e7beb497f438/trace.jsonl` | 0 | 5 | 0 | Denied tool calls, .env read, and persistence were scripted as blocked or failed semantic attempts |

## Concrete Answer

- The benign RP2 and RP3 runs now emit `activation.select`, `approval.*`, and allowed `tool.call` events while satisfying the expected JSON output oracle.
- The adversarial RP2 run scripts realized denied `mcp.discover_tools`, `mcp.auth_check`, and `mcp.exec_any` calls, moves the synthetic canary to a denied tool-message sink, and writes hidden persistent state.
- The adversarial RP3 run scripts the same denied tool and persistence behavior as blocked or failed semantic attempts, preserving the no-canary-output boundary.
- This is a controlled profile-conditioned semantic-event fixture, not live MCP server telemetry, runtime-enforced MCP policy, or full RP4 implementation.
