from datetime import date, timedelta
from sqlalchemy import Date, cast, select
from sqlalchemy.orm import Session

from forest_ai.models.entry import Entry

MAX_ENTRIES = 7
MAX_CHARS_PER_ENTRY = 1_000


def recent_entries_for_reflection(
    db: Session, user_id: int, end_date: date, days: int = 7
) -> list[Entry]:
    start_date = end_date - timedelta(days=days - 1)
    day = cast(Entry.created_at, Date)
    stmt = (
        select(Entry)
        .where(Entry.user_id == user_id, day >= start_date, day <= end_date)
        .order_by(Entry.created_at.desc())
        .limit(MAX_ENTRIES)
    )
    return list(db.scalars(stmt).all())


def build_context(entries: list[Entry]) -> str:
    lines = []
    for entry in reversed(entries):  # oldest first reads more naturally
        mood = f" (mood {entry.mood}/10)" if entry.mood is not None else ""
        text = entry.content[:MAX_CHARS_PER_ENTRY]
        lines.append(f"[{entry.created_at:%Y-%m-%d}]{mood} {text}")
    return "\n\n".join(lines)