"""SkillDiff MVP Python read-provenance shim.

This records Python-level file open attempts for controlled benchmark runs.
It is not syscall-complete tracing.
"""

from __future__ import annotations

import builtins
import hashlib
import json
import os
import pathlib
import threading
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone


_EVENTS_PATH = os.environ.get("SKILLDIFF_FILE_READ_EVENTS")
_WRITE_EVENTS_PATH = os.environ.get("SKILLDIFF_FILE_WRITE_EVENTS")
_WRITE_OBSERVATIONS_PATH = os.environ.get("SKILLDIFF_FILE_WRITE_OBSERVATIONS")
_MODEL = os.environ.get("SKILLDIFF_READ_PROVENANCE_MODEL", "python_sitecustomize_wrapper_mvp")
_NETWORK_EVENTS_PATH = os.environ.get("SKILLDIFF_NETWORK_EVENTS")
_NETWORK_SINK_REQUESTS_PATH = os.environ.get("SKILLDIFF_NETWORK_SINK_REQUESTS")
_NETWORK_MODEL = os.environ.get("SKILLDIFF_NETWORK_PROVENANCE_MODEL", "python_network_shim_mvp")
_NETWORK_MODE = os.environ.get("SKILLDIFF_NETWORK_MODE", "pass_through")
_FAKE_SINK_DOMAINS = {
    value.strip().lower()
    for value in os.environ.get("SKILLDIFF_FAKE_NETWORK_SINK_DOMAINS", "").split(",")
    if value.strip()
}
_CANARY_LABELS = [
    value.strip()
    for value in os.environ.get("SKILLDIFF_CANARY_LABELS", "").split(",")
    if value.strip()
]
_LOCK = threading.Lock()
_ORIGINAL_OPEN = builtins.open
_ORIGINAL_PATH_OPEN = pathlib.Path.open
_ORIGINAL_URLOPEN = urllib.request.urlopen


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _is_read_mode(mode):
    mode = mode or "r"
    return "r" in mode and not any(flag in mode for flag in ("w", "a", "x"))


def _is_write_mode(mode):
    mode = mode or "r"
    return any(flag in mode for flag in ("w", "a", "x", "+"))


def _target(path):
    try:
        return os.fspath(path)
    except TypeError:
        return str(path)


def _append_jsonl(path, row):
    if not path:
        return
    with _ORIGINAL_OPEN(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


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
        _append_jsonl(_EVENTS_PATH, row)


def _append_write_event(path, status, mode, error=None):
    if not _WRITE_EVENTS_PATH and not _WRITE_OBSERVATIONS_PATH:
        return
    row = {
        "event": "filesystem.write",
        "instrumentation_model": "python_failed_write_wrapper_mvp",
        "operation": "write",
        "path": _target(path),
        "status": status,
        "timestamp": _utc_now(),
        "mode": mode or "w",
    }
    if error is not None:
        row["error_type"] = type(error).__name__
        row["error_message"] = str(error)
    with _LOCK:
        _append_jsonl(_WRITE_EVENTS_PATH, row)
        _append_jsonl(_WRITE_OBSERVATIONS_PATH, row)


def _open(path, mode="r", *args, **kwargs):
    if _is_write_mode(mode):
        try:
            return _ORIGINAL_OPEN(path, mode, *args, **kwargs)
        except Exception as exc:
            _append_write_event(path, "failed", mode, exc)
            raise
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
    if _is_write_mode(mode):
        try:
            return _ORIGINAL_PATH_OPEN(self, mode, buffering, encoding, errors, newline)
        except Exception as exc:
            _append_write_event(self, "failed", mode, exc)
            raise
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


class _SkillDiffNetworkBlocked(Exception):
    pass


class _FakeHTTPResponse:
    status = 200
    code = 200
    reason = "OK"

    def __init__(self, body=b'{"ok": true}\n'):
        self._body = body

    def read(self, *args, **kwargs):
        return self._body

    def getcode(self):
        return self.code

    def info(self):
        return {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _request_url(request):
    if hasattr(request, "full_url"):
        return request.full_url
    if hasattr(request, "get_full_url"):
        return request.get_full_url()
    return str(request)


def _request_method(request, data):
    if hasattr(request, "get_method"):
        try:
            return request.get_method()
        except Exception:
            pass
    return "POST" if data is not None else "GET"


def _request_data(request, data):
    if data is not None:
        return data
    return getattr(request, "data", None)


def _payload_bytes(data):
    if data is None:
        return b""
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        return data.encode("utf-8", errors="replace")
    return repr(data).encode("utf-8", errors="replace")


def _sink_type_for_domain(domain):
    return "fake_http" if domain.lower() in _FAKE_SINK_DOMAINS else "external_http"


def _network_row(url, method, data, status, error=None, event=None, operation=None):
    parsed = urllib.parse.urlparse(url)
    domain = parsed.hostname or ""
    payload = _payload_bytes(data)
    labels = []
    try:
        text = payload.decode("utf-8", errors="replace")
    except Exception:
        text = ""
    for label in _CANARY_LABELS:
        if label and label in text:
            labels.append(label)
    row = {
        "event": event or ("network.send" if payload else "network.connect"),
        "instrumentation_model": _NETWORK_MODEL,
        "operation": operation or ("send" if payload else "connect"),
        "url": url,
        "domain": domain,
        "port": parsed.port,
        "scheme": parsed.scheme,
        "method": method,
        "status": status,
        "sink_type": _sink_type_for_domain(domain),
        "timestamp": _utc_now(),
        "payload_hash": "sha256:" + hashlib.sha256(payload).hexdigest() if payload else None,
        "payload_size": len(payload),
        "payload_redacted_excerpt": "<redacted>" if payload else "",
        "canary_labels": sorted(set(labels)),
        "public_internet_contacted": False,
    }
    if error is not None:
        row["error_type"] = type(error).__name__
        row["error_message"] = str(error)
    return row


def _append_network_event(url, method, data, status, error=None, event=None, operation=None):
    if not _NETWORK_EVENTS_PATH:
        return
    row = _network_row(url, method, data, status, error, event, operation)
    with _LOCK:
        with _ORIGINAL_OPEN(_NETWORK_EVENTS_PATH, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _append_sink_request(url, method, data):
    if not _NETWORK_SINK_REQUESTS_PATH:
        return
    row = _network_row(url, method, data, "succeeded", event="network.send", operation="send")
    sink_row = {
        "canary_labels": row["canary_labels"],
        "domain": row["domain"],
        "event": "network.sink_request",
        "instrumentation_model": _NETWORK_MODEL,
        "method": row["method"],
        "payload_hash": row["payload_hash"],
        "payload_redacted_excerpt": row["payload_redacted_excerpt"],
        "payload_size": row["payload_size"],
        "public_internet_contacted": False,
        "scheme": row["scheme"],
        "sink_type": row["sink_type"],
        "status": row["status"],
        "timestamp": row["timestamp"],
        "url": row["url"],
    }
    with _LOCK:
        with _ORIGINAL_OPEN(_NETWORK_SINK_REQUESTS_PATH, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(sink_row, sort_keys=True) + "\n")


def _urlopen(request, data=None, *args, **kwargs):
    url = _request_url(request)
    method = _request_method(request, data)
    body = _request_data(request, data)
    domain = urllib.parse.urlparse(url).hostname or ""
    if _NETWORK_MODE == "fake_sink" and domain.lower() in _FAKE_SINK_DOMAINS:
        _append_network_event(url, method, body, "succeeded")
        _append_sink_request(url, method, body)
        return _FakeHTTPResponse()
    if _NETWORK_MODE == "block":
        error = _SkillDiffNetworkBlocked(f"network blocked by SkillDiff profile for {url}")
        _append_network_event(url, method, None, "failed", error, event="network.connect", operation="connect")
        if body is not None:
            _append_network_event(url, method, body, "failed", error, event="network.send", operation="send")
        raise urllib.error.URLError(error)
    try:
        response = _ORIGINAL_URLOPEN(request, data=data, *args, **kwargs)
    except Exception as exc:
        _append_network_event(url, method, body, "failed", exc)
        raise
    _append_network_event(url, method, body, "succeeded")
    return response


urllib.request.urlopen = _urlopen
