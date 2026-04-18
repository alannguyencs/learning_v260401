"""Slide API endpoints: current slide, forward/back navigation, quiz respond, chat."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from src.auth import authenticate_user_from_request
from src.crud import crud_dashboard, crud_learning_progress
from src.crud.crud_content import (
    get_chapter,
    get_chapter_quiz,
    get_lesson,
    get_lesson_by_chapter_id,
)
from src.crud import crud_slide_like
from src.crud.crud_slide_chat import get_chat_messages, get_recent_chat_messages, save_chat_message
from src.crud.crud_slide_position import save_feedback
from src.crud.crud_slides import log_quiz_skip, remove_quiz_skip
from src.database import get_db
from src.schemas.slides import (
    ChatMessageResponse,
    ChapterLearntResponse,
    LikeListResponse,
    LikeResponse,
    QuizRespondRequest,
    QuizRespondResponse,
    SlideChatRequest,
    SlideChatResponse,
    SlideForwardRequest,
    SlideResponse,
)
from src.service.learning_progress_service import LearningProgressService
from src.service.quiz_grader import QuizGrader
from src.service.revision_service import RevisionService
from src.service.slide_chat_service import SlideChatService
from src.service.slide_navigation import get_current_slide, go_next, go_previous

router = APIRouter()


def require_session_user(request: Request, db: Session = Depends(get_db)):
    """Dependency: require an authenticated session user."""
    user = authenticate_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.get("/slides/current", response_model=SlideResponse)
def slide_current(
    book_id: Optional[str] = None,
    user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Return the user's current slide (saved position or fresh next)."""
    result = get_current_slide(db, user.username, book_id)
    return SlideResponse(
        slide_type=result.slide_type,
        chapter=result.chapter,
        quiz=result.quiz,
        has_previous=result.has_previous,
        feedback=result.feedback,
    )


@router.post("/slides/forward", response_model=SlideResponse)
def slide_forward(
    body: SlideForwardRequest,
    user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Advance to the next slide, optionally marking a chapter as learnt."""
    result = go_next(db, user.username, body.book_id, body.mark_chapter_id)
    return SlideResponse(
        slide_type=result.slide_type,
        chapter=result.chapter,
        quiz=result.quiz,
        has_previous=result.has_previous,
        feedback=result.feedback,
    )


@router.post("/slides/back", response_model=SlideResponse)
def slide_back(
    user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Go to the previous slide."""
    result = go_previous(db, user.username)
    return SlideResponse(
        slide_type=result.slide_type,
        chapter=result.chapter,
        quiz=result.quiz,
        has_previous=result.has_previous,
        feedback=result.feedback,
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
        return QuizRespondResponse(
            is_correct=None, good_points=None, bad_points=None, round_done=result.round_done
        )

    if body.pre_evaluated:
        is_correct = body.is_correct
        good_points = body.good_points
        bad_points = body.bad_points
    elif quiz.quiz_type == "multiple_choice":
        correct_options = quiz.correct_options or []
        user_selections = sorted(body.user_answer.split(","))
        is_correct = user_selections == sorted(correct_options)
        good_points = None
        bad_points = None
    else:
        grading = QuizGrader.grade(
            quiz.question,
            quiz.expected_answer or "",
            body.user_answer,
            quiz.quiz_type,
        )
        is_correct = grading.is_correct
        good_points = grading.good_points
        bad_points = grading.bad_points

    remove_quiz_skip(db, user.username, quiz_id)
    result = RevisionService.record_quiz_response(
        db, user.username, quiz_id, body.lesson_id, body.round_num, is_correct, lesson_count
    )
    crud_dashboard.log_quiz_answer(
        db,
        username=user.username,
        quiz_id=quiz_id,
        lesson_id=body.lesson_id,
        round_num=body.round_num,
        is_correct=is_correct,
    )
    save_feedback(
        db,
        user.username,
        {"is_correct": is_correct, "good_points": good_points, "bad_points": bad_points},
    )
    return QuizRespondResponse(
        is_correct=is_correct,
        good_points=good_points,
        bad_points=bad_points,
        round_done=result.round_done,
    )


def _build_slide_context(db: Session, slide_type: str, chapter_id, quiz_id):
    """Build slide_identifier, slide_context text, and lesson from slide params."""
    if slide_type == "chapter":
        if not chapter_id:
            raise HTTPException(status_code=400, detail="chapter_id required for chapter slides")
        chapter = get_chapter(db, chapter_id)
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")
        lesson = get_lesson(db, chapter.lesson_id)
        return f"chapter:{chapter_id}", chapter.content, lesson

    if slide_type == "quiz":
        if not quiz_id:
            raise HTTPException(status_code=400, detail="quiz_id required for quiz slides")
        quiz = get_chapter_quiz(db, quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        chapter = get_chapter(db, quiz.chapter_id)
        lesson = get_lesson_by_chapter_id(db, quiz.chapter_id)
        context_parts = [f"Quiz question: {quiz.question}"]
        if quiz.expected_answer:
            context_parts.append(f"Expected answer: {quiz.expected_answer}")
        if chapter:
            context_parts.append(f"Chapter content:\n{chapter.content}")
        return f"quiz:{quiz_id}", "\n".join(context_parts), lesson

    raise HTTPException(status_code=400, detail="slide_type must be 'chapter' or 'quiz'")


@router.post("/slides/chat", response_model=SlideChatResponse)
def slide_chat(
    body: SlideChatRequest,
    user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Send a chat message about the current slide and get an AI response."""
    slide_id, slide_context, lesson = _build_slide_context(
        db, body.slide_type, body.chapter_id, body.quiz_id
    )
    raw_content = lesson.raw_content if lesson else None
    recent = get_recent_chat_messages(db, user.username, slide_id, limit=10)

    response_text = SlideChatService.answer(slide_context, raw_content, recent, body.message)

    save_chat_message(db, user.username, slide_id, "user", body.message)
    save_chat_message(db, user.username, slide_id, "assistant", response_text)

    return SlideChatResponse(response=response_text)


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
    """Return the user's liked quiz IDs, newest first."""
    ids = crud_slide_like.get_liked_quiz_ids(db, user.username)
    return LikeListResponse(quiz_ids=ids)


@router.get("/slides/chat", response_model=List[ChatMessageResponse])
def get_slide_chat_history(
    slide_type: str = Query(...),
    chapter_id: Optional[int] = Query(None),
    quiz_id: Optional[int] = Query(None),
    user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Get chat history for a specific slide."""
    slide_id, _, _ = _build_slide_context(db, slide_type, chapter_id, quiz_id)
    messages = get_chat_messages(db, user.username, slide_id)
    return [
        ChatMessageResponse(
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at.isoformat(),
        )
        for msg in messages
    ]
