import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from forest_ai.db.session import engine
from forest_ai.main import app

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


def test_trends_average_mood_per_day():
    headers = _auth_headers("mood1@example.com")
    client.post("/entries", json={"content": "a", "mood": 4}, headers=headers)
    client.post("/entries", json={"content": "b", "mood": 8}, headers=headers)

    response = client.get("/moods/trends", headers=headers)

    assert response.status_code == 200
    points = response.json()["points"]
    assert len(points) == 1
    assert points[0]["average_mood"] == 6.0
    assert points[0]["entry_count"] == 2


def test_entries_without_mood_are_ignored():
    headers = _auth_headers("mood2@example.com")
    client.post("/entries", json={"content": "no mood"}, headers=headers)

    response = client.get("/moods/trends", headers=headers)

    assert response.json()["points"] == []


def test_trends_only_include_own_entries():
    alice = _auth_headers("mood3@example.com")
    bob = _auth_headers("mood4@example.com")
    client.post("/entries", json={"content": "a", "mood": 2}, headers=alice)
    client.post("/entries", json={"content": "b", "mood": 10}, headers=bob)

    points = client.get("/moods/trends", headers=alice).json()["points"]

    assert len(points) == 1
    assert points[0]["average_mood"] == 2.0


def test_invalid_date_range_is_rejected():
    headers = _auth_headers("mood5@example.com")
    response = client.get(
        "/moods/trends?from_date=2026-02-01&to_date=2026-01-01",
        headers=headers,
    )
    assert response.status_code == 400