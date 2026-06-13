"""Tests for the V2V Over Mode WS gate and tool-call routing."""

import asyncio

import pytest
from starlette.websockets import WebSocketDisconnect

from src.api import voice_chat
from src.service.voice_over import tools


# --- WebSocket auth / voice gate ---------------------------------------------


def test_ws_rejects_missing_auth(client):
    """No auth cookie → close 4401 before accept."""
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/api/voice/v2v-over"):
            pass
    assert exc.value.code == 4401


def test_ws_rejects_unknown_voice(client, monkeypatch):
    """Authenticated but unknown ?voice= → close 4001."""

    class _User:
        username = "testuser"

    monkeypatch.setattr(voice_chat, "_authenticate", lambda ws: _User())
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/api/voice/v2v-over?voice=NotAVoice"):
            pass
    assert exc.value.code == 4001


# --- tool-call routing -------------------------------------------------------


class _FC:
    def __init__(self, name, args=None, fc_id="fc1"):
        self.name = name
        self.args = args or {}
        self.id = fc_id


class _ToolCall:
    def __init__(self, fcs):
        self.function_calls = fcs


class _FakeSession:
    def __init__(self):
        self.responses = []

    async def send_tool_response(self, *, function_responses):
        self.responses.append(function_responses)


def test_search_notes_routes_and_responds(monkeypatch):
    monkeypatch.setattr(
        tools,
        "_notes_for_tool",
        lambda q: {"notes": [{"title": "Attention", "rel_path": "p.md", "content": "c"}]},
    )
    sess = _FakeSession()
    tc = _ToolCall([_FC("search_notes", {"query": "attention"})])

    asyncio.run(tools.handle_tool_call(sess, tc, username="alan"))

    assert len(sess.responses) == 1
    fr = sess.responses[0][0]
    assert fr.name == "search_notes"
    assert fr.response["notes"][0]["title"] == "Attention"


def test_history_routes_and_responds(monkeypatch):
    monkeypatch.setattr(
        tools,
        "_history_for_tool",
        lambda username: {"history": [{"user": "q0", "assistant": "a0"}]},
    )
    sess = _FakeSession()
    tc = _ToolCall([_FC("get_conversation_history")])

    asyncio.run(tools.handle_tool_call(sess, tc, username="alan"))

    fr = sess.responses[0][0]
    assert fr.name == "get_conversation_history"
    assert fr.response["history"] == [{"user": "q0", "assistant": "a0"}]


def test_unknown_tool_responds_empty(monkeypatch):
    sess = _FakeSession()
    tc = _ToolCall([_FC("nope")])

    asyncio.run(tools.handle_tool_call(sess, tc, username="alan"))

    fr = sess.responses[0][0]
    assert fr.response == {}


def test_no_function_calls_sends_nothing():
    sess = _FakeSession()
    asyncio.run(tools.handle_tool_call(sess, _ToolCall([]), username="alan"))
    assert sess.responses == []


# --- notes relevance cutoff --------------------------------------------------


class _Hit:
    def __init__(self, score):
        self.score = score


def test_relevant_hits_drops_weak_offtopic():
    # Top hit strong; a far-weaker hit below half the top score is dropped.
    hits = [_Hit(8.0), _Hit(6.0), _Hit(1.0)]

    kept = tools._relevant_hits(hits)

    assert [h.score for h in kept] == [8.0, 6.0]


def test_relevant_hits_drops_negligible_overlap():
    # All hits below the absolute floor → nothing on topic.
    assert tools._relevant_hits([_Hit(0.05), _Hit(0.0)]) == []


def test_relevant_hits_keeps_close_scores():
    # Two notes both clearly on topic (within the relative ratio) → keep both.
    hits = [_Hit(5.0), _Hit(4.0)]

    assert [h.score for h in tools._relevant_hits(hits)] == [5.0, 4.0]
