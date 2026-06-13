-- Migration: voice_conversation_turns
-- One row per completed V2V Over Mode turn; source for the
-- get_conversation_history tool. DDL only, idempotent.

CREATE TABLE IF NOT EXISTS voice_conversation_turns (
    id          SERIAL PRIMARY KEY,
    username    TEXT      NOT NULL REFERENCES users(username),
    session_id  TEXT      NOT NULL,
    turn_index  INTEGER   NOT NULL,
    user_text   TEXT      NOT NULL,
    bot_text    TEXT      NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_voice_conversation_turns_session
    ON voice_conversation_turns (session_id);
