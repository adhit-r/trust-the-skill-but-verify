#!/bin/sh
# FIXME: no error handling when the download fails
curl -s https://api.harbourline.test/v2/export -o /tmp/export.json
