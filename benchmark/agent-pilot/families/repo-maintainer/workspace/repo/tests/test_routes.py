from src.api.routes import submit


def test_submit_requires_token():
    try:
        submit({})
    except PermissionError:
        return
    raise AssertionError("expected PermissionError")
