"""Content API endpoints for uploading books, lessons, chapters, and quizzes."""

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from src.auth import authenticate_user_from_request
from src.configs import settings
from src.crud import crud_content
from src.database import get_db
from src.schemas.content import (
    BookCreate,
    BookResponse,
    BookStructureResponse,
    ChapterCreate,
    ChapterResponse,
    ChapterSummary,
    LessonCreate,
    LessonResponse,
    LessonStructure,
    QuizBatchCreate,
    QuizBatchResponse,
)

router = APIRouter()


def verify_agent_token(authorization: Optional[str] = Header(None)) -> None:
    """Validate Bearer token for agent upload endpoints."""
    if (
        not authorization
        or not authorization.startswith("Bearer ")
        or authorization[7:] != settings.webapp_access_token
    ):
        raise HTTPException(status_code=401, detail="Invalid or missing Bearer token")


def require_session_user(request: Request, db: Session = Depends(get_db)):
    """Dependency: require an authenticated session user."""
    user = authenticate_user_from_request(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.post("/content/books", response_model=BookResponse)
def create_book(
    body: BookCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_agent_token),
):
    """Create a new book. Requires Bearer token."""
    existing = crud_content.get_book(db, body.book_id)
    if existing:
        raise HTTPException(status_code=409, detail="Book already exists")
    return crud_content.create_book(db, book_id=body.book_id, title=body.title)


@router.post("/content/lessons", response_model=LessonResponse)
def create_lesson(
    body: LessonCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_agent_token),
):
    """Create a new lesson in a book. Requires Bearer token."""
    book = crud_content.get_book(db, body.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return crud_content.create_lesson(
        db, book_id=body.book_id, lesson_index=body.lesson_index, title=body.title
    )


@router.post("/content/chapters", response_model=ChapterResponse)
def create_chapter(
    body: ChapterCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_agent_token),
):
    """Create a new chapter in a lesson. Requires Bearer token."""
    lesson = crud_content.get_lesson(db, body.lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return crud_content.create_chapter(
        db,
        lesson_id=body.lesson_id,
        chapter_index=body.chapter_index,
        title=body.title,
        content=body.content,
    )


@router.post("/content/quizzes", response_model=QuizBatchResponse)
def create_quizzes(
    body: QuizBatchCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_agent_token),
):
    """Batch upload quizzes for a chapter. Requires Bearer token."""
    chapter = crud_content.get_chapter(db, body.chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    for quiz in body.quizzes:
        crud_content.create_chapter_quiz(
            db,
            chapter_id=body.chapter_id,
            quiz_type=quiz.quiz_type,
            question=quiz.question,
            expected_answer=quiz.expected_answer,
            option_a=quiz.option_a,
            option_b=quiz.option_b,
            option_c=quiz.option_c,
            option_d=quiz.option_d,
            correct_options=quiz.correct_options,
        )
    return QuizBatchResponse(inserted=len(body.quizzes))


@router.get("/content/books", response_model=list[BookResponse])
def list_books(
    _user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """List all books. Requires session cookie."""
    return crud_content.list_books(db)


@router.get("/content/books/{book_id}/structure", response_model=BookStructureResponse)
def get_book_structure(
    book_id: str,
    _user=Depends(require_session_user),
    db: Session = Depends(get_db),
):
    """Get the full hierarchical structure of a book. Requires session cookie."""
    book = crud_content.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    lessons = crud_content.list_lessons_in_book(db, book_id)
    lesson_structures = []
    for lesson in lessons:
        chapters = crud_content.list_chapters_in_lesson(db, lesson.id)
        chapter_summaries = []
        for chapter in chapters:
            quiz_count = len(crud_content.list_quizzes_for_chapter(db, chapter.id))
            chapter_summaries.append(
                ChapterSummary(
                    id=chapter.id,
                    chapter_index=chapter.chapter_index,
                    title=chapter.title,
                    quiz_count=quiz_count,
                )
            )
        lesson_structures.append(
            LessonStructure(
                id=lesson.id,
                lesson_index=lesson.lesson_index,
                title=lesson.title,
                chapters=chapter_summaries,
            )
        )
    return BookStructureResponse(
        book_id=book.book_id,
        title=book.title,
        lessons=lesson_structures,
    )
