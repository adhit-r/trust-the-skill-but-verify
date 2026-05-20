"""SkillDiff MVP Python read-provenance shim.

This records Python-level file open attempts for controlled benchmark runs.
It is not syscall-complete tracing.
"""

from __future__ import annotations

import builtins
import json
import os
import pathlib
import threading
from datetime import datetime, timezone


_EVENTS_PATH = os.environ.get("SKILLDIFF_FILE_READ_EVENTS")
_MODEL = os.environ.get("SKILLDIFF_READ_PROVENANCE_MODEL", "python_sitecustomize_wrapper_mvp")
_LOCK = threading.Lock()
_ORIGINAL_OPEN = builtins.open
_ORIGINAL_PATH_OPEN = pathlib.Path.open


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _is_read_mode(mode):
    mode = mode or "r"
    return "r" in mode and not any(flag in mode for flag in ("w", "a", "x"))


def _target(path):
    try:
        return os.fspath(path)
    except TypeError:
        return str(path)


def _append_event(path, status, mode, error=None):
    if not _EVENTS_PATH:
        return
    row = {
        "event": "filesystem.read",
        "instrumentation_model": _MODEL,
        "operation": "read",
        "path": _target(path),
        "status": status,
        "timestamp": _utc_now(),
        "mode": mode or "r",
    }
    if error is not None:
        row["error_type"] = type(error).__name__
        row["error_message"] = str(error)
    with _LOCK:
        with _ORIGINAL_OPEN(_EVENTS_PATH, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _open(path, mode="r", *args, **kwargs):
    if not _is_read_mode(mode):
        return _ORIGINAL_OPEN(path, mode, *args, **kwargs)
    try:
        handle = _ORIGINAL_OPEN(path, mode, *args, **kwargs)
    except Exception as exc:
        _append_event(path, "failed", mode, exc)
        raise
    _append_event(path, "succeeded", mode)
    return handle


def _path_open(self, mode="r", buffering=-1, encoding=None, errors=None, newline=None):
    if not _is_read_mode(mode):
        return _ORIGINAL_PATH_OPEN(self, mode, buffering, encoding, errors, newline)
    try:
        handle = _ORIGINAL_PATH_OPEN(self, mode, buffering, encoding, errors, newline)
    except Exception as exc:
        _append_event(self, "failed", mode, exc)
        raise
    _append_event(self, "succeeded", mode)
    return handle


builtins.open = _open
pathlib.Path.open = _path_open
