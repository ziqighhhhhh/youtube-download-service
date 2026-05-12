from fastapi import HTTPException

from services.csrf_service import ensure_csrf_token, require_csrf


class Request:
    def __init__(self, session=None, headers=None):
        self.session = session or {}
        self.headers = headers or {}


def test_ensure_csrf_token_is_stable():
    request = Request()

    token = ensure_csrf_token(request)

    assert token
    assert ensure_csrf_token(request) == token


def test_require_csrf_rejects_missing_token():
    request = Request(session={"csrf_token": "expected"}, headers={})

    try:
        require_csrf(request)
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("CSRF check should fail")


def test_require_csrf_accepts_matching_token():
    request = Request(
        session={"csrf_token": "expected"},
        headers={"x-csrf-token": "expected"},
    )

    require_csrf(request)
