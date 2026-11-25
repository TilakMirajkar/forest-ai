from datetime import datetime
from pydantic import BaseModel

from forest_ai.schemas.entry import EntryOut


class SearchResult(EntryOut):
    distance: float