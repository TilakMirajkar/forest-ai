from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session

from forest_ai.db.session import get_db
from forest_ai.deps import get_current_user
from forest_ai.models.entry import Entry
from forest_ai.models.user import User
from forest_ai.schemas.insight import DayHighlight, WeeklySummary

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/summary", response_model=WeeklySummary)
def weekly_summary(
    end_date: date = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    end_date = end_date or date.today()
    start_date = end_date - timedelta(days=6)  # 7 days including end_date

    day = cast(Entry.created_at, Date)
    in_range = [
        Entry.user_id == user.id,
        day >= start_date,
        day <= end_date,
    ]

    totals = db.execute(
        select(
            func.count(Entry.id),
            func.count(func.distinct(day)),
            func.avg(Entry.mood),
        ).where(*in_range)
    ).one()
    entry_count, active_days, avg_mood = totals

    # Per-day averages, only for days that have at least one rated entry
    daily = (
        select(
            day.label("day"),
            func.avg(Entry.mood).label("avg_mood"),
        )
        .where(*in_range, Entry.mood.is_not(None))
        .group_by(day)
        .subquery()
    )

    best = db.execute(
        select(daily.c.day, daily.c.avg_mood)
        .order_by(daily.c.avg_mood.desc(), daily.c.day.desc())
        .limit(1)
    ).first()
    hardest = db.execute(
        select(daily.c.day, daily.c.avg_mood)
        .order_by(daily.c.avg_mood.asc(), daily.c.day.desc())
        .limit(1)
    ).first()

    def to_highlight(row) -> DayHighlight | None:
        if row is None:
            return None
        return DayHighlight(day=row.day, average_mood=round(float(row.avg_mood), 2))

    return WeeklySummary(
        from_date=start_date,
        to_date=end_date,
        entry_count=entry_count,
        active_days=active_days,
        average_mood=round(float(avg_mood), 2) if avg_mood is not None else None,
        best_day=to_highlight(best),
        hardest_day=to_highlight(hardest),
    )