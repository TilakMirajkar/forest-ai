from datetime import datetime
from sqlalchemy import text

from forest_ai.db.session import engine


def insert_entry(user_id: int, mood: int | None, created_at: datetime,
                 content: str = "test entry") -> None:
    """Insert an entry with an explicit timestamp, bypassing the API."""
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO entries (user_id, content, mood, created_at, updated_at) "
                "VALUES (:user_id, :content, :mood, :created_at, :created_at)"
            ),
            {"user_id": user_id, "content": content, "mood": mood,
             "created_at": created_at},
        )


def user_id_for(email: str) -> int:
    with engine.connect() as conn:
        return conn.execute(
            text("SELECT id FROM users WHERE email = :email"), {"email": email}
        ).scalar_one()