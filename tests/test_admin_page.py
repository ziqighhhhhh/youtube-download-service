from fastapi.testclient import TestClient

from main import app


def test_admin_page_requires_login():
    client = TestClient(app)

    response = client.get("/admin", follow_redirects=False)

    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/login"
