from fastapi.testclient import TestClient

from main import app


def test_admin_page_requires_login():
    client = TestClient(app)

    response = client.get("/admin", follow_redirects=False)

    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/login"


def test_csrf_token_rendered_on_login_page():
    client = TestClient(app)

    response = client.get("/login")

    assert response.status_code == 200
    assert "CSRF_TOKEN" in response.text
