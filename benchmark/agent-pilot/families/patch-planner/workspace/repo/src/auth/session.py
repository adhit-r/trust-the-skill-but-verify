"""Session cookies."""

IDLE_TIMEOUT = 1800


def build_cookie(session_id, secure=True):
    flags = ["HttpOnly"]
    if secure:
        flags.append("Secure")
    return f"sid={session_id}; " + "; ".join(flags)


def is_expired(last_seen, now):
    return now - last_seen > IDLE_TIMEOUT


def revoke(store, session_id):
    store.pop(session_id, None)
