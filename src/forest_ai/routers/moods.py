from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session

from forest_ai.db.session import get_db
from forest_ai.deps import get_current_user
from forest_ai.models.entry import Entry
from forest_ai.models.user import User
from forest_ai.schemas.mood import MoodPoint, MoodTrends

router = APIRouter(prefix="/moods", tags=["moods"])


@router.get("/trends", response_model=MoodTrends)
def mood_trends(
    from_date: date = Query(default=None),
    to_date: date = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    to_date = to_date or date.today()
    from_date = from_date or to_date - timedelta(days=30)

    if from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_date must be on or before to_date",
        )

    day = cast(Entry.created_at, Date).label("day")
    stmt = (
        select(
            day,
            func.avg(Entry.mood).label("average_mood"),
            func.count(Entry.id).label("entry_count"),
        )
        .where(
            Entry.user_id == user.id,
            Entry.mood.is_not(None),
            cast(Entry.created_at, Date) >= from_date,
            cast(Entry.created_at, Date) <= to_date,
        )
        .group_by(day)
        .order_by(day)
    )

    rows = db.execute(stmt).all()
    points = [
        MoodPoint(day=row.day, average_mood=round(float(row.average_mood), 2),
                  entry_count=row.entry_count)
        for row in rows
    ]
    return MoodTrends(from_date=from_date, to_date=to_date, points=points)