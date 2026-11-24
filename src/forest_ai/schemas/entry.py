from datetime import datetime
from pydantic import BaseModel, Field


class EntryCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10_000)
    mood: int | None = Field(default=None, ge=1, le=10)


class EntryUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1, max_length=10_000)
    mood: int | None = Field(default=None, ge=1, le=10)


class EntryOut(BaseModel):
    id: int
    content: str
    mood: int | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}