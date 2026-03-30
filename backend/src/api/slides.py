"""Slide API endpoints: next slide, mark chapter learnt, quiz respond."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.auth import authenticate_user_from_request
from src.crud import crud_learning_progress
from src.crud.crud_content import get_chapter_quiz
from src.crud.crud_slides import log_quiz_skip, remove_quiz_skip
from src.database import get_db
from src.schemas.slides import (
    ChapterLearntResponse,
    QuizRespondRequest,
    QuizRespondResponse,
    SlideResponse,
)
from src.service.learning_progress_service import LearningProgressService
from src.service.quiz_grader import QuizGrader
from src.service.revision_service import RevisionService
from src.service.slide_selector import SlideSelector

router = APIRouter()


def require_session_user(request: Request, db: Session = Depends(get_db)):
    """Dependency: require an authenticated session user."""
    user = authenticate_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.get("/slides/next", response_model=SlideResponse)
def get_next_slide(
    book_id: Optional[str] = None,
    user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Return the next slide for the authenticated user (3-tier priority)."""
    result = SlideSelector.get_next_slide(db, user.username, book_id)
    return SlideResponse(
        slide_type=result.slide_type,
        chapter=result.chapter,
        quiz=result.quiz,
    )


@router.post("/slides/chapters/{chapter_id}/learnt", response_model=ChapterLearntResponse)
def mark_chapter_learnt(
    chapter_id: int,
    user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Mark a chapter as learnt and distribute its quizzes into revision rounds."""
    lp_result = LearningProgressService.mark_chapter_learnt(db, user.username, chapter_id)
    RevisionService.on_chapter_learnt(
        db,
        user.username,
        lp_result.lesson_id,
        lp_result.chapter_quiz_ids,
        lp_result.lesson_count,
    )
    return ChapterLearntResponse(
        lesson_fully_learnt=lp_result.lesson_fully_learnt,
        lesson_count=lp_result.lesson_count,
    )


@router.post("/slides/quizzes/{quiz_id}/respond", response_model=QuizRespondResponse)
def respond_to_quiz(
    quiz_id: int,
    body: QuizRespondRequest,
    user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Submit a quiz answer or skip. Grades the answer and updates revision state."""
    quiz = get_chapter_quiz(db, quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz not found")

    lesson_count = crud_learning_progress.get_lesson_count(db, user.username)

    if body.is_skip:
        log_quiz_skip(db, user.username, quiz_id, body.lesson_id, body.round_num)
        result = RevisionService.record_quiz_response(
            db, user.username, quiz_id, body.lesson_id, body.round_num, None, lesson_count
        )
        return QuizRespondResponse(is_correct=None, feedback=None, round_done=result.round_done)

    if quiz.quiz_type == "multiple_choice":
        correct_options = quiz.correct_options or []
        is_correct = body.user_answer in correct_options
        feedback = None
    else:
        grading = QuizGrader.grade(
            quiz.question,
            quiz.expected_answer or "",
            body.user_answer,
            quiz.quiz_type,
        )
        is_correct = grading.is_correct
        feedback = grading.feedback

    remove_quiz_skip(db, user.username, quiz_id)
    result = RevisionService.record_quiz_response(
        db, user.username, quiz_id, body.lesson_id, body.round_num, is_correct, lesson_count
    )
    return QuizRespondResponse(
        is_correct=is_correct,
        feedback=feedback,
        round_done=result.round_done,
    )
