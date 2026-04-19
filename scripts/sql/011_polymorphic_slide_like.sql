-- Migration: Polymorphic user_slide_like (quiz likes + chapter likes)
-- Extends 010_user_slide_like.sql so a like row can target either a quiz or a chapter.
-- DDL only, idempotent

-- 1. Relax NOT NULL on quiz_id so chapter-like rows can omit it
ALTER TABLE user_slide_like
    ALTER COLUMN quiz_id DROP NOT NULL;

-- 2. Add nullable chapter_id with FK to chapters(id)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user_slide_like' AND column_name = 'chapter_id'
    ) THEN
        ALTER TABLE user_slide_like
            ADD COLUMN chapter_id INTEGER NULL REFERENCES chapters(id);
    END IF;
END
$$;

-- 3. Enforce exactly-one-of (quiz_id, chapter_id) at DB layer
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'usl_exactly_one_target'
    ) THEN
        ALTER TABLE user_slide_like
            ADD CONSTRAINT usl_exactly_one_target
            CHECK ((quiz_id IS NOT NULL) <> (chapter_id IS NOT NULL));
    END IF;
END
$$;

-- 4. Chapter-leg uniqueness and lookup index
CREATE UNIQUE INDEX IF NOT EXISTS idx_usl_user_chapter_unique
    ON user_slide_like (username, chapter_id);

CREATE INDEX IF NOT EXISTS idx_usl_chapter
    ON user_slide_like (chapter_id);
