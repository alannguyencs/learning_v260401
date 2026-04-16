CREATE TABLE IF NOT EXISTS slide_position (
    username VARCHAR PRIMARY KEY REFERENCES users(username),
    slide_type VARCHAR NOT NULL,
    slide_id INTEGER NOT NULL,
    lesson_id INTEGER,
    round_num INTEGER,
    feedback_json JSONB,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
