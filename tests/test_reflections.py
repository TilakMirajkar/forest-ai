import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from forest_ai.db.session import engine
from forest_ai.main import app
from forest_ai.services.ai import AIServiceError

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_tables():
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE users, entries RESTART IDENTITY CASCADE"))
    yield


def _auth_headers(email: str) -> dict[str, str]:
    client.post("/auth/register", json={"email": email, "password": "password123"})
    login = client.post(
        "/auth/token",
        data={"username": email, "password": "password123"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
def fake_model(monkeypatch):
    def _fake(context: str) -> str:
        return "What felt most meaningful about your week?"

    monkeypatch.setattr(
        "forest_ai.routers.reflections.generate_reflection", _fake
    )


def test_reflection_returns_question(fake_model):
    headers = _auth_headers("ref1@example.com")
    client.post("/entries", json={"content": "Long walk today", "mood": 7}, headers=headers)

    response = client.post("/reflections", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["question"] == "What felt most meaningful about your week?"
    assert body["based_on_entries"] == 1


def test_reflection_without_entries_returns_404(fake_model):
    headers = _auth_headers("ref2@example.com")
    response = client.post("/reflections", headers=headers)
    assert response.status_code == 404


def test_model_outage_returns_503(monkeypatch):
    def _broken(context: str) -> str:
        raise AIServiceError("Local model is unavailable")

    monkeypatch.setattr(
        "forest_ai.routers.reflections.generate_reflection", _broken
    )
    headers = _auth_headers("ref3@example.com")
    client.post("/entries", json={"content": "Some thoughts"}, headers=headers)

    response = client.post("/reflections", headers=headers)

    assert response.status_code == 503


def test_context_includes_only_own_entries(monkeypatch):
    captured = {}

    def _capture(context: str) -> str:
        captured["context"] = context
        return "A question?"

    monkeypatch.setattr(
        "forest_ai.routers.reflections.generate_reflection", _capture
    )
    alice = _auth_headers("ref4@example.com")
    bob = _auth_headers("ref5@example.com")
    client.post("/entries", json={"content": "Alice secret"}, headers=alice)
    client.post("/entries", json={"content": "Bob secret"}, headers=bob)

    client.post("/reflections", headers=alice)

    assert "Alice secret" in captured["context"]
    assert "Bob secret" not in captured["context"]