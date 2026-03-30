-- Migration: Revision Scheduling
-- Creates lesson_revision_rounds and user_quiz_recall tables

CREATE TABLE IF NOT EXISTS lesson_revision_rounds (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL REFERENCES users(username),
    lesson_id INTEGER NOT NULL REFERENCES lessons(id),
    round_num INTEGER NOT NULL DEFAULT 0,
    status VARCHAR NOT NULL DEFAULT 'open',
    due_at_lesson_count INTEGER NOT NULL DEFAULT 0,
    completed_at_lesson_count INTEGER,
    quizzes_in_round INTEGER NOT NULL DEFAULT 0,
    quizzes_answered INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(username, lesson_id, round_num)
);
CREATE INDEX IF NOT EXISTS idx_lrr_user_status ON lesson_revision_rounds(username, status);
CREATE INDEX IF NOT EXISTS idx_lrr_user_lesson ON lesson_revision_rounds(username, lesson_id);

CREATE TABLE IF NOT EXISTS user_quiz_recall (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL REFERENCES users(username),
    quiz_id INTEGER NOT NULL REFERENCES chapter_quizzes(id),
    forgetting_rate FLOAT NOT NULL DEFAULT 1.0,
    last_reviewed_lesson_count INTEGER,
    review_count INTEGER NOT NULL DEFAULT 0,
    UNIQUE(username, quiz_id)
);
CREATE INDEX IF NOT EXISTS idx_uqr_user ON user_quiz_recall(username);
