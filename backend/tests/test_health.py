import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("src.main.get_database_url", lambda: None)
    return TestClient(app)


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["database_configured"] is False


def test_list_items_without_database(client: TestClient):
    r = client.get("/api/items")
    assert r.status_code == 200
    assert r.json()["items"] == []
