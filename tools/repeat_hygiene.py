#!/usr/bin/env python3
"""Shared repeat-ID helpers for runner wrappers."""

from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_REPEAT_ID = 1


def positive_repeat_id(value: str | int) -> int:
    repeat_id = int(value)
    if repeat_id < DEFAULT_REPEAT_ID:
        raise argparse.ArgumentTypeError("repeat ID must be >= 1")
    return repeat_id


def add_repeat_id_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--repeat-id",
        type=positive_repeat_id,
        default=DEFAULT_REPEAT_ID,
        help="Repeat ID to stamp into traces and generated findings. Defaults to 1.",
    )


def repeat_suffix(repeat_id: int) -> str:
    return "" if repeat_id == DEFAULT_REPEAT_ID else f"_repeat{repeat_id}"


def repeat_stem(stem: str, repeat_id: int) -> str:
    return f"{stem}{repeat_suffix(repeat_id)}"


def repeat_path(path: Path, repeat_id: int) -> Path:
    if repeat_id == DEFAULT_REPEAT_ID:
        return path
    return path.with_name(f"{path.stem}{repeat_suffix(repeat_id)}{path.suffix}")


def repeat_seed(seed: str, repeat_id: int) -> str:
    return seed if repeat_id == DEFAULT_REPEAT_ID else f"{seed}-repeat{repeat_id}"
