-- Migration: terminology_notes
-- Postgres-backed mirror of terminologies/notes/ with precomputed BM25 stats.
-- Powers the voice tutor's search_notes tool. DDL only, idempotent.

CREATE TABLE IF NOT EXISTS terminology_notes (
    id            SERIAL PRIMARY KEY,
    rel_path      TEXT        NOT NULL UNIQUE,
    title         TEXT        NOT NULL,
    raw_content   TEXT        NOT NULL,
    terminologies JSONB       NOT NULL DEFAULT '[]'::jsonb,
    token_length  INTEGER     NOT NULL,
    term_freq     JSONB       NOT NULL DEFAULT '{}'::jsonb,
    updated_at    TIMESTAMP   NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_terminology_notes_rel_path
    ON terminology_notes (rel_path);
