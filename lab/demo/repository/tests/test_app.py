from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_healthz() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "customer-portal"}


def test_demo_login() -> None:
    response = client.post(
        "/api/login",
        json={"username": "demo.user", "password": "DemoPortal-Only-2026!"},
    )
    assert response.status_code == 200
    assert response.json()["authenticated"] is True

