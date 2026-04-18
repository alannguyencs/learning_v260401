-- Migration: User Slide Like
-- Persists per-user quiz likes; drives the filled/outline heart UI
-- DDL only, idempotent

CREATE TABLE IF NOT EXISTS user_slide_like (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL REFERENCES users(username),
    quiz_id INTEGER NOT NULL REFERENCES chapter_quizzes(id),
    liked_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(username, quiz_id)
);
CREATE INDEX IF NOT EXISTS idx_usl_user ON user_slide_like(username);
