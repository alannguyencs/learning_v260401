"""Tests for voice conversation history CRUD (Tool #1's source)."""

from src.crud import crud_voice_conversation as crud


def _add(db, session_id, turn_index, user_text="hi", bot_text="hello", username="testuser"):
    return crud.add_turn(
        db,
        username=username,
        session_id=session_id,
        turn_index=turn_index,
        user_text=user_text,
        bot_text=bot_text,
    )


def test_add_turn_persists_fields(db_session):
    turn = _add(db_session, "sess-a", 0, user_text="what is attention?", bot_text="it lets...")

    assert turn.id is not None
    assert turn.session_id == "sess-a"
    assert turn.turn_index == 0
    assert turn.user_text == "what is attention?"
    assert turn.bot_text == "it lets..."


def test_recent_turns_chronological_order(db_session):
    for i in range(3):
        _add(db_session, "sess-a", i, user_text=f"q{i}", bot_text=f"a{i}")

    turns = crud.recent_turns(db_session, "sess-a", limit=10)

    assert [t.turn_index for t in turns] == [0, 1, 2]
    assert [t.user_text for t in turns] == ["q0", "q1", "q2"]


def test_recent_turns_limit_keeps_latest(db_session):
    for i in range(5):
        _add(db_session, "sess-a", i, user_text=f"q{i}")

    turns = crud.recent_turns(db_session, "sess-a", limit=2)

    # Two newest turns, still oldest-first within the window.
    assert [t.turn_index for t in turns] == [3, 4]


def test_recent_turns_scoped_by_session(db_session):
    _add(db_session, "sess-a", 0, user_text="a0")
    _add(db_session, "sess-b", 0, user_text="b0")

    turns = crud.recent_turns(db_session, "sess-a")

    assert len(turns) == 1
    assert turns[0].user_text == "a0"


def test_recent_turns_empty_session(db_session):
    assert crud.recent_turns(db_session, "no-such-session") == []


def test_recent_turns_for_user_spans_sessions_chronologically(db_session):
    # Two separate sessions for the same user — refresh should restore both.
    _add(db_session, "sess-a", 0, user_text="a0")
    _add(db_session, "sess-a", 1, user_text="a1")
    _add(db_session, "sess-b", 0, user_text="b0")

    turns = crud.recent_turns_for_user(db_session, "testuser", limit=10)

    assert [t.user_text for t in turns] == ["a0", "a1", "b0"]


def test_recent_turns_for_user_scoped_by_username(db_session):
    _add(db_session, "sess-a", 0, user_text="mine", username="testuser")
    _add(db_session, "sess-a", 0, user_text="theirs", username="other")

    turns = crud.recent_turns_for_user(db_session, "testuser")

    assert [t.user_text for t in turns] == ["mine"]


def test_recent_turns_for_user_limit_keeps_latest(db_session):
    for i in range(5):
        _add(db_session, "sess-a", i, user_text=f"q{i}")

    turns = crud.recent_turns_for_user(db_session, "testuser", limit=2)

    # Two newest turns, still oldest-first within the window.
    assert [t.user_text for t in turns] == ["q3", "q4"]
