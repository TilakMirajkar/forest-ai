from datetime import date
from pydantic import BaseModel


class DayHighlight(BaseModel):
    day: date
    average_mood: float


class WeeklySummary(BaseModel):
    from_date: date
    to_date: date
    entry_count: int
    active_days: int
    average_mood: float | None
    best_day: DayHighlight | None
    hardest_day: DayHighlight | None