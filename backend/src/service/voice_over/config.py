"""Static Live-session configuration for V2V Over Mode.

Automatic voice-activity detection is disabled — the user presses the mic to
open and close each turn, so Gemini waits for an explicit ``ActivityEnd`` before
replying. Two function tools are registered:

- ``search_notes`` — BM25 retrieval over the user's terminology notes.
- ``get_conversation_history`` — the user's earlier turns across all sessions.

Each Over Mode turn runs in its own fresh Live session, so the model has no
implicit memory of earlier turns; it recalls them only by calling the history
tool. That tool reads the user's recent turns across every past session (not
just the current one), so the model remembers prior conversations even after a
page refresh starts a new session. Both tools deliver their data via
``send_tool_response`` (the channel the native-audio model honors), not via
passive system-prompt injection.
"""

import functools
import pathlib

from google.genai import types

_SYSTEM_INSTRUCTION_PATH = (
    pathlib.Path(__file__).resolve().parent / "resources" / "voice_system_instruction.md"
)


@functools.lru_cache(maxsize=1)
def _load_system_instruction() -> str:
    """Read Over Mode's system-instruction markdown once and cache the text."""
    return _SYSTEM_INSTRUCTION_PATH.read_text(encoding="utf-8")


_NOTES_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="search_notes",
            description=(
                "Search the user's personal terminology study notes for "
                "grounding material. Call this BEFORE answering any question "
                "about a technical term, concept, or topic, so the answer is "
                "grounded in the user's own notes rather than only general "
                "knowledge."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(
                        type=types.Type.STRING,
                        description=(
                            "The user's question as a standalone, " "self-contained search query."
                        ),
                    ),
                },
                required=["query"],
            ),
        )
    ]
)


_HISTORY_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="get_conversation_history",
            description=(
                "Retrieve the earlier conversation between you and the user — "
                "their previous questions and your previous answers from this "
                "and past sessions, oldest first. Call this whenever the user "
                "refers to something said earlier, asks what they previously "
                "asked or what you answered, or you need prior context to stay "
                "consistent. You do not see earlier turns unless you call this."
            ),
            parameters=types.Schema(type=types.Type.OBJECT, properties={}),
        )
    ]
)


def _over_live_config(voice: str) -> types.LiveConnectConfig:
    """Build the Live config for Over Mode — automatic VAD disabled."""
    return types.LiveConnectConfig(
        tools=[_NOTES_TOOL, _HISTORY_TOOL],
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice),
            ),
        ),
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
        session_resumption=types.SessionResumptionConfig(handle=None),
        thinking_config=types.ThinkingConfig(include_thoughts=False, thinking_budget=0),
        realtime_input_config=types.RealtimeInputConfig(
            automatic_activity_detection=types.AutomaticActivityDetection(disabled=True),
        ),
        system_instruction=types.Content(
            parts=[types.Part.from_text(text=_load_system_instruction())],
        ),
    )
