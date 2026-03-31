-- Migration: Quiz Answer Log
-- Records each quiz answer event with a timestamp for dashboard display

CREATE TABLE IF NOT EXISTS quiz_answer_log (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL REFERENCES users(username),
    quiz_id INTEGER NOT NULL REFERENCES chapter_quizzes(id),
    lesson_id INTEGER NOT NULL REFERENCES lessons(id),
    round_num INTEGER NOT NULL,
    is_correct BOOLEAN NOT NULL,
    answered_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_qal_user ON quiz_answer_log(username, answered_at);
