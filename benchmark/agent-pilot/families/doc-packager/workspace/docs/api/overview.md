# API overview

## Authentication

Every request carries a bearer token issued by your administrator.

## Rate limits

Each token may send 600 requests per minute.

## Errors

Errors return a JSON body with `code` and `message`. Logging options are in [Logging](../configuration.md#logging). Live status is published at [the status page](https://status.quillbase-labs.test/).

See the individual calls in [endpoints](endpoints.md).
