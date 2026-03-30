-- Migration: Slide Skip Log
-- Tracks skipped quizzes for Tier 3 resurface

CREATE TABLE IF NOT EXISTS quiz_skip_log (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL REFERENCES users(username),
    quiz_id INTEGER NOT NULL REFERENCES chapter_quizzes(id),
    lesson_id INTEGER NOT NULL REFERENCES lessons(id),
    round_num INTEGER NOT NULL,
    skipped_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_qsl_user ON quiz_skip_log(username, skipped_at);
