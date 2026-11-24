from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from forest_ai.db.session import get_db
from forest_ai.deps import get_current_user
from forest_ai.models.user import User
from forest_ai.schemas.reflection import ReflectionOut
from forest_ai.services.ai import AIServiceError, generate_reflection
from forest_ai.services.reflections import build_context, recent_entries_for_reflection

router = APIRouter(prefix="/reflections", tags=["reflections"])


@router.post("", response_model=ReflectionOut)
def create_reflection(
    end_date: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    end_date = end_date or date.today()
    entries = recent_entries_for_reflection(db, user.id, end_date)

    if not entries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recent entries to reflect on",
        )

    try:
        question = generate_reflection(build_context(entries))
    except AIServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return ReflectionOut(
        question=question,
        based_on_entries=len(entries),
        from_date=end_date - timedelta(days=6),
        to_date=end_date,
    )