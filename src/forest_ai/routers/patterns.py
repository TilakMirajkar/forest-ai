from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Date, Integer, cast, func, select
from sqlalchemy.orm import Session

from forest_ai.db.session import get_db
from forest_ai.deps import get_current_user
from forest_ai.models.entry import Entry
from forest_ai.models.user import User
from forest_ai.schemas.patterns import Patterns, WeekdayMood, WeekOverWeek

router = APIRouter(prefix="/insights", tags=["insights"])

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday",
                 "Friday", "Saturday", "Sunday"]


def _avg(db: Session, user_id: int, start: date, end: date) -> tuple[float | None, int]:
    day = cast(Entry.created_at, Date)
    avg, count = db.execute(
        select(func.avg(Entry.mood), func.count(Entry.id)).where(
            Entry.user_id == user_id,
            Entry.mood.is_not(None),
            day >= start,
            day <= end,
        )
    ).one()
    return (round(float(avg), 2) if avg is not None else None, count)


@router.get("/patterns", response_model=Patterns)
def patterns(
    weeks: int = Query(default=4, ge=2, le=52),
    end_date: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    end_date = end_date or date.today()
    start_date = end_date - timedelta(weeks=weeks) + timedelta(days=1)

    # Mood and count per weekday (Postgres EXTRACT(DOW) returns 0=Sunday, so convert)
    dow = cast(func.extract("isodow", Entry.created_at), Integer) - 1  # 0=Monday
    rows = db.execute(
        select(
            dow.label("weekday"),
            func.avg(Entry.mood).label("avg_mood"),
            func.count(Entry.id).label("entry_count"),
        )
        .where(
            Entry.user_id == user.id,
            cast(Entry.created_at, Date) >= start_date,
            cast(Entry.created_at, Date) <= end_date,
        )
        .group_by(dow)
    ).all()
    by_day = {row.weekday: row for row in rows}

    by_weekday = []
    for i, name in enumerate(WEEKDAY_NAMES):
        row = by_day.get(i)
        by_weekday.append(WeekdayMood(
            weekday=i,
            weekday_name=name,
            average_mood=round(float(row.avg_mood), 2)
            if row and row.avg_mood is not None else None,
            entry_count=row.entry_count if row else 0,
        ))

    rated = [w for w in by_weekday if w.average_mood is not None]
    lowest = min(rated, key=lambda w: w.average_mood).weekday_name if rated else None

    # Week over week: last 7 days vs the 7 days before
    current_start = end_date - timedelta(days=6)
    previous_start = current_start - timedelta(days=7)
    previous_end = current_start - timedelta(days=1)

    current_avg, _ = _avg(db, user.id, current_start, end_date)
    previous_avg, _ = _avg(db, user.id, previous_start, previous_end)
    change = (
        round(current_avg - previous_avg, 2)
        if current_avg is not None and previous_avg is not None
        else None
    )

    return Patterns(
        from_date=start_date,
        to_date=end_date,
        by_weekday=by_weekday,
        week_over_week=WeekOverWeek(
            current_week_start=current_start,
            previous_week_start=previous_start,
            current_average_mood=current_avg,
            previous_average_mood=previous_avg,
            change=change,
        ),
        lowest_mood_weekday=lowest,
    )