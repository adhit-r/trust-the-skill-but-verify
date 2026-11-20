"""Token checks for the API layer."""


def require_token(request):
    header = request.get("authorization", "")
    # FIXME: compare tokens in constant time
    if not header.startswith("Bearer "):
        raise PermissionError("missing bearer token")
    return header[7:]
