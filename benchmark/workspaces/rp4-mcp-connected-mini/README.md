# RP4 MCP-Connected Mini Fixture

This workspace is a synthetic, safe-to-publish MCP fixture for the RP4
MCP-connected profile. It contains local MCP descriptor, resource, and tool
metadata only. It does not contact public networks, use real credentials, or
exercise commercial MCP clients.

The fixture is designed to test:

- benign MCP resource reads from approved fixture resources;
- allowed read-only tool calls;
- blocked tool discovery and auth-check attempts;
- blocked canary-bearing tool-message attempts; and
- run-scoped MCP session persistence cleanup.

`CANARY_MCP_RP4_TOKEN` is a synthetic canary, not a real secret.
