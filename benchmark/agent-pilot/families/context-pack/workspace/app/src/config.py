"""Static configuration for the parcel tracker."""

DEFAULTS = {"start": "2026-01-01", "end": "2026-12-31", "port": 8080}


def load_config() -> dict:
    return dict(DEFAULTS)
