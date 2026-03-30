CREATE TABLE IF NOT EXISTS user_chapter_progress (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL REFERENCES users(username),
    chapter_id INTEGER NOT NULL REFERENCES chapters(id),
    learnt_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(username, chapter_id)
);
CREATE INDEX IF NOT EXISTS idx_ucp_user ON user_chapter_progress(username);
CREATE INDEX IF NOT EXISTS idx_ucp_user_chapter ON user_chapter_progress(username, chapter_id);

CREATE TABLE IF NOT EXISTS user_lesson_count (
    username VARCHAR PRIMARY KEY REFERENCES users(username),
    total_lessons_learnt INTEGER NOT NULL DEFAULT 0
);
