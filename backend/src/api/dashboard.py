"""Dashboard API endpoints: activity log and learning progress."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.auth import authenticate_user_from_request
from src.crud import crud_dashboard
from src.database import get_db

router = APIRouter()


class ActivityLogEntry(BaseModel):
    """A single row in the user activity log."""

    event_time: Optional[datetime]
    action: str
    book_id: Optional[str]
    lesson_index: Optional[int]
    lesson_title: Optional[str]
    chapter_id: Optional[int]
    answer_result: Optional[str]
    forgetting_rate: Optional[float]

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class LessonProgress(BaseModel):
    """Per-lesson metrics within a book progress card."""

    lesson_title: str
    round_num: Optional[int]
    round_status: Optional[str]
    total_answers: int
    correct_answers: int


class BookProgressEntry(BaseModel):
    """Per-book progress card with lesson table and accuracy trendline."""

    book_id: str
    book_title: str
    lessons: List[LessonProgress]
    accuracy_trend: List[int]


def require_session_user(request: Request, db: Session = Depends(get_db)):
    """Dependency: require an authenticated session user."""
    user = authenticate_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.get("/dashboard/activity-log", response_model=List[ActivityLogEntry])
def get_activity_log(
    user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Return the full chronological activity log for the authenticated user."""
    rows = crud_dashboard.get_activity_log(db, user.username)
    return [ActivityLogEntry(**row) for row in rows]


@router.get(
    "/dashboard/learning-progress",
    response_model=List[BookProgressEntry],
)
def get_learning_progress(
    user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Return per-book progress with lesson table and accuracy trend."""
    return crud_dashboard.get_learning_progress(db, user.username)
