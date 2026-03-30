CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    book_id VARCHAR UNIQUE NOT NULL,
    title VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS lessons (
    id SERIAL PRIMARY KEY,
    book_id VARCHAR NOT NULL REFERENCES books(book_id),
    lesson_index INTEGER NOT NULL,
    title VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(book_id, lesson_index)
);
CREATE INDEX IF NOT EXISTS idx_lessons_book ON lessons(book_id);

CREATE TABLE IF NOT EXISTS chapters (
    id SERIAL PRIMARY KEY,
    lesson_id INTEGER NOT NULL REFERENCES lessons(id),
    chapter_index INTEGER NOT NULL,
    title VARCHAR NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(lesson_id, chapter_index)
);
CREATE INDEX IF NOT EXISTS idx_chapters_lesson ON chapters(lesson_id);

CREATE TABLE IF NOT EXISTS chapter_quizzes (
    id SERIAL PRIMARY KEY,
    chapter_id INTEGER NOT NULL REFERENCES chapters(id),
    quiz_type VARCHAR NOT NULL,
    question TEXT NOT NULL,
    expected_answer TEXT,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    correct_options JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cq_chapter ON chapter_quizzes(chapter_id);
