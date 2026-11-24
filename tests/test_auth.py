import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from forest_ai.db.session import engine
from forest_ai.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_users_table():
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE users RESTART IDENTITY CASCADE"))
    yield


def test_register_creates_user():
    response = client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_rejects_duplicate_email():
    payload = {"email": "bob@example.com", "password": "password123"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 409


def test_login_returns_token_and_me_works():
    client.post(
        "/auth/register",
        json={"email": "carol@example.com", "password": "password123"},
    )
    login = client.post(
        "/auth/token",
        data={"username": "carol@example.com", "password": "password123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "carol@example.com"


def test_login_rejects_wrong_password():
    client.post(
        "/auth/register",
        json={"email": "dave@example.com", "password": "password123"},
    )
    response = client.post(
        "/auth/token",
        data={"username": "dave@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_me_without_token_is_unauthorized():
    response = client.get("/auth/me")
    assert response.status_code == 401