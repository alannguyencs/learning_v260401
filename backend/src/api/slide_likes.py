"""Slide like API endpoints: quiz + chapter likes, /likes, /liked-items, /liked-quizzes."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.auth import authenticate_user_from_request
from src.crud import crud_learning_progress, crud_slide_like
from src.crud.crud_content import get_chapter, get_chapter_quiz
from src.database import get_db
from src.schemas.slides import (
    FavoriteChapter,
    FavoriteListResponse,
    FavoriteQuiz,
    LikeListResponse,
    LikeResponse,
    LikedChapterItem,
    LikedItemsResponse,
    LikedQuizItem,
)
from src.service.revision_service import RevisionService

router = APIRouter()


def require_session_user(request: Request, db: Session = Depends(get_db)):
    """Dependency: require an authenticated session user."""
    user = authenticate_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.post("/slides/quizzes/{quiz_id}/like", response_model=LikeResponse)
def like_quiz(
    quiz_id: int,
    user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Like a quiz: record the like and boost its forgetting rate."""
    if get_chapter_quiz(db, quiz_id) is None:
        raise HTTPException(status_code=404, detail="Quiz not found")
    crud_slide_like.add_like(db, user.username, quiz_id)
    lesson_count = crud_learning_progress.get_lesson_count(db, user.username)
    RevisionService.apply_like_boost(db, user.username, quiz_id, lesson_count)
    return LikeResponse(liked=True)


@router.delete("/slides/quizzes/{quiz_id}/like", response_model=LikeResponse)
def unlike_quiz(
    quiz_id: int,
    user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Unlike a quiz; forgetting_rate is not restored."""
    crud_slide_like.remove_like(db, user.username, quiz_id)
    return LikeResponse(liked=False)


@router.get("/slides/likes", response_model=LikeListResponse)
def list_likes(
    user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Return the user's liked quiz and chapter IDs, newest first per leg."""
    quiz_ids = crud_slide_like.get_liked_quiz_ids(db, user.username)
    chapter_ids = crud_slide_like.get_liked_chapter_ids(db, user.username)
    return LikeListResponse(quiz_ids=quiz_ids, chapter_ids=chapter_ids)


@router.get("/slides/liked-quizzes", response_model=FavoriteListResponse)
def list_liked_quizzes(
    user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Return full quiz detail for each liked quiz, newest like first (legacy)."""
    rows = crud_slide_like.get_liked_quizzes_with_context(db, user.username)
    quizzes = [
        FavoriteQuiz(
            id=quiz.id,
            chapter_id=quiz.chapter_id,
            quiz_type=quiz.quiz_type,
            question=quiz.question,
            option_a=quiz.option_a,
            option_b=quiz.option_b,
            option_c=quiz.option_c,
            option_d=quiz.option_d,
            expected_answer=quiz.expected_answer,
            lesson_id=lesson.id,
            lesson_title=lesson.title,
            book_id=book.book_id,
            book_title=book.title,
            section_name=quiz.section_name,
            quiz_take_away=quiz.quiz_take_away,
            quiz_metadata=quiz.quiz_metadata,
            correct_options=quiz.correct_options,
            liked_at=like.liked_at.isoformat(),
        )
        for like, quiz, lesson, book in rows
    ]
    return FavoriteListResponse(quizzes=quizzes)


@router.post("/slides/chapters/{chapter_id}/like", response_model=LikeResponse)
def like_chapter(
    chapter_id: int,
    user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Like a chapter; bookmark only — no effect on slide selection."""
    if get_chapter(db, chapter_id) is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    crud_slide_like.add_chapter_like(db, user.username, chapter_id)
    return LikeResponse(liked=True)


@router.delete("/slides/chapters/{chapter_id}/like", response_model=LikeResponse)
def unlike_chapter(
    chapter_id: int,
    user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Unlike a chapter; idempotent."""
    crud_slide_like.remove_chapter_like(db, user.username, chapter_id)
    return LikeResponse(liked=False)


def _row_to_quiz_item(row) -> LikedQuizItem:
    """Convert a quiz LikedItemRow into a LikedQuizItem."""
    quiz = row.quiz
    return LikedQuizItem(
        id=row.like_id,
        liked_at=row.liked_at.isoformat(),
        quiz=FavoriteQuiz(
            id=quiz.id,
            chapter_id=quiz.chapter_id,
            quiz_type=quiz.quiz_type,
            question=quiz.question,
            option_a=quiz.option_a,
            option_b=quiz.option_b,
            option_c=quiz.option_c,
            option_d=quiz.option_d,
            expected_answer=quiz.expected_answer,
            lesson_id=row.lesson_id,
            lesson_title=row.lesson_title,
            book_id=row.book_id,
            book_title=row.book_title,
            section_name=quiz.section_name,
            quiz_take_away=quiz.quiz_take_away,
            quiz_metadata=quiz.quiz_metadata,
            correct_options=quiz.correct_options,
            liked_at=row.liked_at.isoformat(),
        ),
    )


def _row_to_chapter_item(row) -> LikedChapterItem:
    """Convert a chapter LikedItemRow into a LikedChapterItem."""
    chapter = row.chapter
    return LikedChapterItem(
        id=row.like_id,
        liked_at=row.liked_at.isoformat(),
        chapter=FavoriteChapter(
            id=chapter.id,
            lesson_id=row.lesson_id,
            lesson_title=row.lesson_title,
            lesson_index=row.lesson_index,
            chapter_index=chapter.chapter_index,
            book_id=row.book_id,
            book_title=row.book_title,
            title=chapter.title,
            content=chapter.content,
        ),
    )


@router.get("/slides/liked-items", response_model=LikedItemsResponse)
def list_liked_items(
    user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Return liked quizzes and chapters interleaved, newest-like first."""
    rows = crud_slide_like.get_liked_items_with_context(db, user.username)
    items = []
    for row in rows:
        if row.kind == "quiz" and row.quiz is not None:
            items.append(_row_to_quiz_item(row))
        elif row.kind == "chapter" and row.chapter is not None:
            items.append(_row_to_chapter_item(row))
    return LikedItemsResponse(items=items)
