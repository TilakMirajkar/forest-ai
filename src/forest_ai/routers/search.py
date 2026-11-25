from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from forest_ai.db.session import get_db
from forest_ai.deps import get_current_user
from forest_ai.models.entry import Entry
from forest_ai.models.user import User
from forest_ai.schemas.search import SearchResult
from forest_ai.services.ai import AIServiceError, embed_text

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=list[SearchResult])
def semantic_search(
    q: str = Query(min_length=1, max_length=500),
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        query_vector = embed_text(q)
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=str(exc)) from exc

    distance = Entry.embedding.cosine_distance(query_vector).label("distance")
    stmt = (
        select(Entry, distance)
        .where(Entry.user_id == user.id, Entry.embedding.is_not(None))
        .order_by(distance)
        .limit(limit)
    )

    results = []
    for entry, dist in db.execute(stmt).all():
        results.append(SearchResult(
            id=entry.id,
            content=entry.content,
            mood=entry.mood,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
            distance=round(float(dist), 4),
        ))
    return results