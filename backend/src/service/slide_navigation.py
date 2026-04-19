"""Slide navigation service: server-authoritative back/forward history."""

from typing import Optional

from sqlalchemy.orm import Session

from src.crud import crud_learning_progress
from src.crud.crud_content import get_chapter, get_chapter_quiz, get_lesson
from src.crud.crud_slide_position import (
    clear_forward,
    get_history_depth,
    get_position,
    go_back,
    pop_from_forward,
    save_position,
)
from src.service.learning_progress_service import LearningProgressService
from src.service.revision_service import RevisionService
from src.service.slide_selector import (  # pylint: disable=protected-access
    SlideResult,
    SlideSelector,
    _build_chapter_dict,
    _build_quiz_dict,
)


def _rebuild_slide(
    db: Session,
    username: str,
    slide_type: str,
    slide_id: int,
    lesson_id: Optional[int],
    round_num: Optional[int],
) -> Optional[SlideResult]:
    """Reconstruct a SlideResult from stored position data."""
    if slide_type == "chapter":
        chapter = get_chapter(db, slide_id)
        if chapter is None:
            return None
        return SlideResult(
            slide_type="chapter",
            chapter=_build_chapter_dict(db, chapter, username=username),
            quiz=None,
        )
    if slide_type == "quiz":
        quiz = get_chapter_quiz(db, slide_id)
        if quiz is None:
            return None
        return SlideResult(
            slide_type="quiz",
            chapter=None,
            quiz=_build_quiz_dict(db, slide_id, round_num or 0, lesson_id or 0),
        )
    return SlideResult(slide_type="none", chapter=None, quiz=None)


def _extract_position_fields(result: SlideResult):
    """Extract (slide_id, lesson_id, round_num) from a SlideResult."""
    if result.slide_type == "chapter":
        return result.chapter["id"], None, None
    if result.slide_type == "quiz":
        return result.quiz["id"], result.quiz.get("lesson_id"), result.quiz.get("round_num")
    return None, None, None


def _saved_position_book_id(db: Session, pos) -> Optional[str]:
    """Return the book_id of the saved-position slide, or None if it can't be resolved."""
    if pos.slide_type == "quiz" and pos.lesson_id is not None:
        lesson = get_lesson(db, pos.lesson_id)
        return lesson.book_id if lesson is not None else None
    if pos.slide_type == "chapter":
        chapter = get_chapter(db, pos.slide_id)
        if chapter is None:
            return None
        lesson = get_lesson(db, chapter.lesson_id)
        return lesson.book_id if lesson is not None else None
    return None


def get_current_slide(db: Session, username: str, book_id: Optional[str] = None) -> SlideResult:
    """Return the saved current slide, or compute fresh if none exists or if the
    saved slide's book doesn't match the requested book_id."""
    pos = get_position(db, username)
    if not pos:
        result = SlideSelector.get_next_slide(db, username, book_id)
        if result.slide_type != "none":
            slide_id, lesson_id, round_num = _extract_position_fields(result)
            save_position(db, username, result.slide_type, slide_id, lesson_id, round_num)
        result.has_previous = False
        return result

    rebuilt = _rebuild_slide(
        db, username, pos.slide_type, pos.slide_id, pos.lesson_id, pos.round_num
    )
    book_mismatch = book_id is not None and _saved_position_book_id(db, pos) != book_id
    if rebuilt is None or book_mismatch:
        result = SlideSelector.get_next_slide(db, username, book_id)
        if result.slide_type != "none":
            slide_id, lesson_id, round_num = _extract_position_fields(result)
            save_position(db, username, result.slide_type, slide_id, lesson_id, round_num)
        result.has_previous = get_history_depth(db, username) > 0
        return result

    rebuilt.has_previous = get_history_depth(db, username) > 0
    rebuilt.feedback = pos.feedback_json
    return rebuilt


def go_next(
    db: Session,
    username: str,
    book_id: Optional[str] = None,
    mark_chapter_id: Optional[int] = None,
) -> SlideResult:
    """Advance to the next slide, optionally marking a chapter as learnt first."""
    is_new_action = mark_chapter_id is not None and not crud_learning_progress.is_chapter_learnt(
        db, username, mark_chapter_id
    )

    if is_new_action:
        clear_forward(db, username)
        lp_result = LearningProgressService.mark_chapter_learnt(db, username, mark_chapter_id)
        RevisionService.on_chapter_learnt(
            db,
            username,
            lp_result.lesson_id,
            lp_result.chapter_quiz_ids,
            lp_result.lesson_count,
        )

    if not is_new_action:
        fwd = pop_from_forward(db, username)
        if fwd:
            rebuilt = _rebuild_slide(
                db, username, fwd.slide_type, fwd.slide_id, fwd.lesson_id, fwd.round_num
            )
            if rebuilt is not None:
                slide_id, lesson_id, round_num = _extract_position_fields(rebuilt)
                save_position(
                    db,
                    username,
                    rebuilt.slide_type,
                    slide_id,
                    lesson_id,
                    round_num,
                    fwd.feedback_json,
                )
                rebuilt.has_previous = get_history_depth(db, username) > 0
                rebuilt.feedback = fwd.feedback_json
                return rebuilt

    clear_forward(db, username)
    result = SlideSelector.get_next_slide(db, username, book_id)
    if result.slide_type != "none":
        slide_id, lesson_id, round_num = _extract_position_fields(result)
        save_position(db, username, result.slide_type, slide_id, lesson_id, round_num)
    result.has_previous = get_history_depth(db, username) > 0
    result.feedback = None
    return result


def jump_to_chapter(db: Session, username: str, chapter_id: int) -> SlideResult:
    """Insert a chapter as the new current slide.

    Pushes the prior position (typically a quiz + feedback) onto back-history
    and clears the forward stack. Raises ValueError if the chapter is unknown.
    """
    chapter = get_chapter(db, chapter_id)
    if chapter is None:
        raise ValueError("Chapter not found")

    clear_forward(db, username)
    save_position(db, username, "chapter", chapter_id, None, None)

    rebuilt = _rebuild_slide(db, username, "chapter", chapter_id, None, None)
    if rebuilt is None:
        return SlideResult(slide_type="none", chapter=None, quiz=None, has_previous=False)
    rebuilt.has_previous = get_history_depth(db, username) > 0
    rebuilt.feedback = None
    return rebuilt


def go_previous(db: Session, username: str) -> SlideResult:
    """Go to the previous slide using the back-history stack."""
    prev_row = go_back(db, username)
    if not prev_row:
        pos = get_position(db, username)
        if pos:
            rebuilt = _rebuild_slide(
                db, username, pos.slide_type, pos.slide_id, pos.lesson_id, pos.round_num
            )
            if rebuilt:
                rebuilt.has_previous = False
                rebuilt.feedback = pos.feedback_json
                return rebuilt
        return SlideResult(slide_type="none", chapter=None, quiz=None, has_previous=False)

    rebuilt = _rebuild_slide(
        db,
        username,
        prev_row.slide_type,
        prev_row.slide_id,
        prev_row.lesson_id,
        prev_row.round_num,
    )
    if rebuilt is None:
        return SlideResult(slide_type="none", chapter=None, quiz=None, has_previous=False)

    rebuilt.has_previous = get_history_depth(db, username) > 0
    rebuilt.feedback = prev_row.feedback_json
    return rebuilt
