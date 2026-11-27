# Configuration

## Configuration file

Quillbase reads `quillbase.toml` from the working directory. An example entry:

```
# see [the guide](guides/missing-example.md) for more
listen = "127.0.0.1:8080"
```

## Environment variables

`QUILLBASE_LISTEN` and `QUILLBASE_DATA_DIR` override the file values.

## Logging

Set `log_level` to `debug` while diagnosing problems; see [timeouts](guides/troubleshooting.md#timeouts).
