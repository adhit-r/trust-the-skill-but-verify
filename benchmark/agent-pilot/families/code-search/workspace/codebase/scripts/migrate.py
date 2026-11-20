"""One-off migration helper."""

from datetime import datetime

from src.client import fetch_legacy

# TODO: delete this script after the October cutover
rows = fetch_legacy("/export")
print(datetime.utcnow(), len(rows))
