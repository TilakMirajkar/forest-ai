from datetime import date

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


def test_summary_with_no_entries():
    headers = _auth_headers("ins1@example.com")

    response = client.get("/insights/summary", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["entry_count"] == 0
    assert body["active_days"] == 0
    assert body["average_mood"] is None
    assert body["best_day"] is None
    assert body["hardest_day"] is None


def test_summary_counts_and_averages():
    headers = _auth_headers("ins2@example.com")
    client.post("/entries", json={"content": "a", "mood": 4}, headers=headers)
    client.post("/entries", json={"content": "b", "mood": 8}, headers=headers)
    client.post("/entries", json={"content": "c"}, headers=headers)

    body = client.get("/insights/summary", headers=headers).json()

    assert body["entry_count"] == 3
    assert body["active_days"] == 1
    assert body["average_mood"] == 6.0
    assert body["best_day"]["average_mood"] == 6.0
    assert body["hardest_day"]["average_mood"] == 6.0


def test_summary_ignores_entries_outside_range():
    headers = _auth_headers("ins3@example.com")
    client.post("/entries", json={"content": "today", "mood": 7}, headers=headers)

    # A window ending 30 days ago contains none of today's entries
    body = client.get(
        "/insights/summary?end_date=2020-01-07", headers=headers
    ).json()

    assert body["entry_count"] == 0
    assert body["from_date"] == "2020-01-01"
    assert body["to_date"] == "2020-01-07"


def test_summary_only_includes_own_entries():
    alice = _auth_headers("ins4@example.com")
    bob = _auth_headers("ins5@example.com")
    client.post("/entries", json={"content": "a", "mood": 3}, headers=alice)
    client.post("/entries", json={"content": "b", "mood": 9}, headers=bob)

    body = client.get("/insights/summary", headers=alice).json()

    assert body["entry_count"] == 1
    assert body["average_mood"] == 3.0