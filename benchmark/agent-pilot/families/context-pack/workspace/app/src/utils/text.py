"""Text helpers."""

import re


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def truncate(value: str, limit: int = 60) -> str:
    return value if len(value) <= limit else value[: limit - 1] + "…"
