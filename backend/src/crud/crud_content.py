"""CRUD operations for content models: Book, Lesson, Chapter, ChapterQuiz."""

from typing import List, Optional

from sqlalchemy.orm import Session

from src.models.content import Book, Chapter, ChapterQuiz, Lesson


def get_book(db: Session, book_id: str) -> Optional[Book]:
    """Get a book by book_id."""
    return db.query(Book).filter(Book.book_id == book_id).first()


def create_book(db: Session, book_id: str, title: str) -> Book:
    """Create a new book."""
    db_book = Book(book_id=book_id, title=title)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


def list_books(db: Session) -> List[Book]:
    """List all books."""
    return db.query(Book).order_by(Book.book_id).all()


def get_lesson(db: Session, lesson_id: int) -> Optional[Lesson]:
    """Get a lesson by id."""
    return db.query(Lesson).filter(Lesson.id == lesson_id).first()


def create_lesson(db: Session, book_id: str, lesson_index: int, title: str) -> Lesson:
    """Create a new lesson in a book."""
    db_lesson = Lesson(book_id=book_id, lesson_index=lesson_index, title=title)
    db.add(db_lesson)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson


def list_lessons_in_book(db: Session, book_id: str) -> List[Lesson]:
    """List all lessons in a book ordered by lesson_index."""
    return db.query(Lesson).filter(Lesson.book_id == book_id).order_by(Lesson.lesson_index).all()


def get_lesson_chapter_count(db: Session, lesson_id: int) -> int:
    """Count chapters in a lesson."""
    return db.query(Chapter).filter(Chapter.lesson_id == lesson_id).count()


def get_chapter(db: Session, chapter_id: int) -> Optional[Chapter]:
    """Get a chapter by id."""
    return db.query(Chapter).filter(Chapter.id == chapter_id).first()


def create_chapter(
    db: Session, lesson_id: int, chapter_index: int, title: str, content: str
) -> Chapter:
    """Create a new chapter in a lesson."""
    db_chapter = Chapter(
        lesson_id=lesson_id, chapter_index=chapter_index, title=title, content=content
    )
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)
    return db_chapter


def list_chapters_in_lesson(db: Session, lesson_id: int) -> List[Chapter]:
    """List all chapters in a lesson ordered by chapter_index."""
    return (
        db.query(Chapter)
        .filter(Chapter.lesson_id == lesson_id)
        .order_by(Chapter.chapter_index)
        .all()
    )


def create_chapter_quiz(
    db: Session,
    chapter_id: int,
    quiz_type: str,
    question: str,
    expected_answer: Optional[str],
    option_a: Optional[str],
    option_b: Optional[str],
    option_c: Optional[str],
    option_d: Optional[str],
    correct_options: Optional[list],
) -> ChapterQuiz:
    """Create a quiz question for a chapter."""
    db_quiz = ChapterQuiz(
        chapter_id=chapter_id,
        quiz_type=quiz_type,
        question=question,
        expected_answer=expected_answer,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct_options=correct_options,
    )
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)
    return db_quiz


def list_quizzes_for_chapter(db: Session, chapter_id: int) -> List[ChapterQuiz]:
    """List all quizzes for a chapter."""
    return db.query(ChapterQuiz).filter(ChapterQuiz.chapter_id == chapter_id).all()


def list_quizzes_for_lesson(db: Session, lesson_id: int) -> List[ChapterQuiz]:
    """List all quizzes for all chapters in a lesson."""
    return (
        db.query(ChapterQuiz)
        .join(Chapter, ChapterQuiz.chapter_id == Chapter.id)
        .filter(Chapter.lesson_id == lesson_id)
        .all()
    )
