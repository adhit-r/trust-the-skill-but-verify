"""Access and refresh tokens."""

import secrets

_refresh = {}


def issue(user_id):
    token = secrets.token_urlsafe(32)
    _refresh[token] = user_id
    return token


def refresh(token):
    user_id = _refresh.pop(token)
    return issue(user_id)


def validate(token):
    return bool(token) and token in _refresh
