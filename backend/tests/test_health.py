import pytest
from fastapi.testclient import TestClient
from src.main import app


def _no_database_url():
    return None


def _no_database(monkeypatch) -> None:
    """All modules that keep a `get_database_url` import must see a disabled DB in tests."""
    monkeypatch.setattr("src.utils.db.get_database_url", _no_database_url)
    monkeypatch.setattr("src.utils.deps.get_database_url", _no_database_url)
    monkeypatch.setattr("src.main.get_database_url", _no_database_url)


@pytest.fixture
def client(monkeypatch):
    _no_database(monkeypatch)
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


def test_signup_without_database(client: TestClient):
    r = client.post(
        "/api/auth/signup",
        json={"email": "a@b.co", "password": "password12"},
    )
    assert r.status_code == 503
    assert "database" in r.json()["detail"].lower()


def test_password_hash_accepts_long_password():
    from src.apps.users.auth import hash_password, verify_password

    long_pw = "x" * 200
    hashed = hash_password(long_pw)
    assert verify_password(long_pw, hashed)


def test_password_verify_legacy_raw_bcrypt():
    """Hashes created with bcrypt(raw password) before SHA-256 pre-hashing."""
    import bcrypt

    from src.apps.users.auth import verify_password

    raw = b"password12"
    hashed = bcrypt.hashpw(raw, bcrypt.gensalt()).decode("ascii")
    assert verify_password("password12", hashed)
