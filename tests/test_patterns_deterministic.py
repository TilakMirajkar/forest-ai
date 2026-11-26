from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from forest_ai.db.session import engine
from forest_ai.main import app
from tests.helpers import insert_entry, user_id_for

client = TestClient(app)

END = date(2026, 11, 25)  # a Wednesday, fixed so the tests never drift


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


def _at(day: date, hour: int = 12) -> datetime:
    return datetime(day.year, day.month, day.day, hour)


def test_week_over_week_change_is_exact():
    headers = _auth_headers("det1@example.com")
    uid = user_id_for("det1@example.com")
    # Current window: Nov 19 to Nov 25. Previous: Nov 12 to Nov 18.
    insert_entry(uid, 8, _at(date(2026, 11, 20)))  # current avg 8
    insert_entry(uid, 6, _at(date(2026, 11, 22)))  # current avg 7 with the next line
    insert_entry(uid, 6, _at(date(2026, 11, 24)))
    insert_entry(uid, 4, _at(date(2026, 11, 14)))  # previous avg 4

    body = client.get(f"/insights/patterns?end_date={END.isoformat()}",
                      headers=headers).json()
    wow = body["week_over_week"]

    assert wow["current_average_mood"] == 6.67
    assert wow["previous_average_mood"] == 4.0
    assert wow["change"] == 2.67


def test_lowest_weekday_is_exact():
    headers = _auth_headers("det2@example.com")
    uid = user_id_for("det2@example.com")
    # Mon Nov 16 (2026-11-16 is a Monday) rated 2, Wed Nov 18 rated 9
    insert_entry(uid, 2, _at(date(2026, 11, 16)))
    insert_entry(uid, 9, _at(date(2026, 11, 18)))

    body = client.get(f"/insights/patterns?end_date={END.isoformat()}",
                      headers=headers).json()

    assert body["lowest_mood_weekday"] == "Monday"
    assert body["by_weekday"][0]["average_mood"] == 2.0
    assert body["by_weekday"][2]["average_mood"] == 9.0


def test_entries_outside_window_are_ignored():
    headers = _auth_headers("det3@example.com")
    uid = user_id_for("det3@example.com")
    insert_entry(uid, 1, _at(date(2025, 1, 1)))  # far outside the window

    body = client.get(f"/insights/patterns?end_date={END.isoformat()}",
                      headers=headers).json()

    assert body["lowest_mood_weekday"] is None
    assert body["week_over_week"]["current_average_mood"] is None