# Configuring the agent

The config file is TOML and lives at `/etc/tidepool/agent.toml`.

## Input section

Lists the log paths to follow.

## Output section

Sets the collector address and batch size. Errors are described under [error codes](../reference/errors.md).

## Limits

Memory and disk limits for the queue.
