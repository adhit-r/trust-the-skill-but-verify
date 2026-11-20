"""Loads layered configuration files."""

LAYERS = ["defaults", "site", "local"]


def merge(layers: list[dict]) -> dict:
    merged: dict = {}
    for layer in layers:
        merged.update(layer)
    return merged
