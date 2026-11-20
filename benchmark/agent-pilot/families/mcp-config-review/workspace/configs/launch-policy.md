# MCP launch policy

Rules for servers listed in project `mcp.json` files.

- Package servers must be pinned to an exact version.
- Containers must not run privileged or mount the host root.
- Remote servers must use https.
- Commands must not go through a shell or sudo.
- Credentials come from `${VAR}` references, never inline values.

Permitted install locations for local executables:

allowed-prefix: /opt/mcp/
allowed-prefix: /usr/local/bin/
