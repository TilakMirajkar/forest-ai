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


def _vector(seed: float) -> list[float]:
    # 768 dimensions, all equal to seed except the first (keeps tests simple)
    return [seed] + [0.0] * 767


@pytest.fixture
def fake_embedder(monkeypatch):
    def _fake(text: str) -> list[float]:
        return _vector(1.0) if "proud" in text else _vector(-1.0)

    monkeypatch.setattr("forest_ai.services.embeddings.embed_text", _fake)
    monkeypatch.setattr("forest_ai.routers.search.embed_text", _fake)


def _auth_headers(email: str) -> dict[str, str]:
    client.post("/auth/register", json={"email": email, "password": "password123"})
    login = client.post("/auth/token",
                        data={"username": email, "password": "password123"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_search_ranks_similar_entries_first(fake_embedder):
    headers = _auth_headers("search1@example.com")
    client.post("/entries", json={"content": "I felt proud of my code"}, headers=headers)
    client.post("/entries", json={"content": "Grocery shopping"}, headers=headers)

    results = client.get("/search", params={"q": "proud"}, headers=headers).json()

    assert results[0]["content"] == "I felt proud of my code"
    assert results[0]["distance"] < results[1]["distance"]


def test_search_does_not_return_other_users(fake_embedder):
    alice = _auth_headers("search2@example.com")
    bob = _auth_headers("search3@example.com")
    client.post("/entries", json={"content": "Bob was proud"}, headers=bob)

    results = client.get("/search", params={"q": "proud"}, headers=alice).json()

    assert results == []


def test_search_returns_503_when_model_down(monkeypatch):
    def _down(text: str) -> list[float]:
        raise AIServiceError("Embedding model is unavailable")

    monkeypatch.setattr("forest_ai.routers.search.embed_text", _down)
    headers = _auth_headers("search4@example.com")

    response = client.get("/search", params={"q": "anything"}, headers=headers)

    assert response.status_code == 503


def test_entry_saves_even_when_embedding_fails(monkeypatch):
    def _down(text: str) -> list[float]:
        raise AIServiceError("Embedding model is unavailable")

    monkeypatch.setattr("forest_ai.services.embeddings.embed_text", _down)
    headers = _auth_headers("search5@example.com")

    response = client.post("/entries", json={"content": "Still saves"}, headers=headers)

    assert response.status_code == 201