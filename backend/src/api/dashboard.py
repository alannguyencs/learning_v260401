"""Dashboard API endpoints: activity log."""

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


class LessonProgressEntry(BaseModel):
    """Per-lesson progress metrics for the learning progress tab."""

    lesson_id: int
    book_id: str
    book_title: str
    lesson_index: int
    lesson_title: str
    total_chapters: int
    learnt_chapters: int
    round_num: Optional[int]
    round_status: Optional[str]
    quizzes_in_round: Optional[int]
    round_quizzes_answered: Optional[int]
    total_answers: int
    correct_answers: int
    avg_forgetting_rate: Optional[float]


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
    response_model=List[LessonProgressEntry],
)
def get_learning_progress(
    user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Return per-lesson progress metrics for the authenticated user."""
    rows = crud_dashboard.get_learning_progress(db, user.username)
    return [LessonProgressEntry(**row) for row in rows]
