from datetime import date

from pydantic import BaseModel


class ReflectionOut(BaseModel):
    question: str
    based_on_entries: int
    from_date: date
    to_date: date