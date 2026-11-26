from datetime import date, timedelta

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
    login = client.post("/auth/token",
                        data={"username": email, "password": "password123"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_patterns_empty_account():
    headers = _auth_headers("pat1@example.com")
    body = client.get("/insights/patterns", headers=headers).json()

    assert len(body["by_weekday"]) == 7
    assert body["lowest_mood_weekday"] is None
    assert body["week_over_week"]["change"] is None


def test_lowest_mood_weekday_is_detected(monkeypatch):
    headers = _auth_headers("pat2@example.com")
    client.post("/entries", json={"content": "a", "mood": 8}, headers=headers)

    body = client.get("/insights/patterns", headers=headers).json()

    today = date.today()
    expected_index = today.weekday()  # 0 = Monday ... 6 = Sunday
    assert body["by_weekday"][expected_index]["entry_count"] == 1
    assert body["lowest_mood_weekday"] == body["by_weekday"][expected_index]["weekday_name"]


def test_week_over_week_change():
    headers = _auth_headers("pat3@example.com")
    end = date.today()
    # Entries are stamped at creation time, so we only test the math on
    # current week averages by writing rated entries now.
    client.post("/entries", json={"content": "x", "mood": 6}, headers=headers)
    body = client.get("/insights/patterns", headers=headers).json()

    wow = body["week_over_week"]
    assert wow["current_average_mood"] == 6.0
    assert wow["previous_average_mood"] is None
    assert wow["change"] is None


def test_patterns_only_include_own_entries():
    alice = _auth_headers("pat4@example.com")
    bob = _auth_headers("pat5@example.com")
    client.post("/entries", json={"content": "a", "mood": 2}, headers=alice)
    client.post("/entries", json={"content": "b", "mood": 10}, headers=bob)

    body = client.get("/insights/patterns", headers=alice).json()

    assert body["week_over_week"]["current_average_mood"] == 2.0