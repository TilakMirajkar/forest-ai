from datetime import date
from pydantic import BaseModel


class WeekdayMood(BaseModel):
    weekday: int  # 0 = Monday ... 6 = Sunday, matching Python's date.weekday()
    weekday_name: str
    average_mood: float | None
    entry_count: int


class WeekOverWeek(BaseModel):
    current_week_start: date
    previous_week_start: date
    current_average_mood: float | None
    previous_average_mood: float | None
    change: float | None  # current minus previous, None if either week has no ratings


class Patterns(BaseModel):
    from_date: date
    to_date: date
    by_weekday: list[WeekdayMood]
    week_over_week: WeekOverWeek
    lowest_mood_weekday: str | None