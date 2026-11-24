from datetime import date

from pydantic import BaseModel


class MoodPoint(BaseModel):
    day: date
    average_mood: float
    entry_count: int


class MoodTrends(BaseModel):
    from_date: date
    to_date: date
    points: list[MoodPoint]