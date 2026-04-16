CREATE TABLE IF NOT EXISTS slide_history (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL REFERENCES users(username),
    position INTEGER NOT NULL,
    slide_type VARCHAR NOT NULL,
    slide_id INTEGER NOT NULL,
    lesson_id INTEGER,
    round_num INTEGER,
    feedback_json JSONB,
    direction VARCHAR NOT NULL DEFAULT 'back',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_slide_history_user_pos
    ON slide_history(username, position);
