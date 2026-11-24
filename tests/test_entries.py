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


def test_create_and_get_entry():
    headers = _auth_headers("eve@example.com")

    created = client.post(
        "/entries", json={"content": "Good day", "mood": 8}, headers=headers
    )
    assert created.status_code == 201
    entry_id = created.json()["id"]

    fetched = client.get(f"/entries/{entry_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["content"] == "Good day"


def test_update_only_changes_sent_fields():
    headers = _auth_headers("frank@example.com")
    entry_id = client.post(
        "/entries", json={"content": "Original", "mood": 5}, headers=headers
    ).json()["id"]

    response = client.patch(f"/entries/{entry_id}", json={"mood": 9}, headers=headers)

    assert response.status_code == 200
    assert response.json()["content"] == "Original"
    assert response.json()["mood"] == 9


def test_delete_entry():
    headers = _auth_headers("grace@example.com")
    entry_id = client.post(
        "/entries", json={"content": "To delete"}, headers=headers
    ).json()["id"]

    assert client.delete(f"/entries/{entry_id}", headers=headers).status_code == 204
    assert client.get(f"/entries/{entry_id}", headers=headers).status_code == 404


def test_users_cannot_access_each_others_entries():
    owner = _auth_headers("owner@example.com")
    intruder = _auth_headers("intruder@example.com")

    entry_id = client.post(
        "/entries", json={"content": "Private"}, headers=owner
    ).json()["id"]

    assert client.get(f"/entries/{entry_id}", headers=intruder).status_code == 404
    assert client.patch(
        f"/entries/{entry_id}", json={"mood": 1}, headers=intruder
    ).status_code == 404
    assert client.delete(f"/entries/{entry_id}", headers=intruder).status_code == 404


def test_list_only_returns_own_entries():
    alice = _auth_headers("alice2@example.com")
    bob = _auth_headers("bob2@example.com")

    client.post("/entries", json={"content": "Alice 1"}, headers=alice)
    client.post("/entries", json={"content": "Alice 2"}, headers=alice)
    client.post("/entries", json={"content": "Bob 1"}, headers=bob)

    response = client.get("/entries", headers=alice)
    assert response.status_code == 200
    contents = [e["content"] for e in response.json()]
    assert sorted(contents) == ["Alice 1", "Alice 2"]


def test_validation_rejects_bad_mood():
    headers = _auth_headers("heidi@example.com")
    response = client.post(
        "/entries", json={"content": "Hi", "mood": 11}, headers=headers
    )
    assert response.status_code == 422