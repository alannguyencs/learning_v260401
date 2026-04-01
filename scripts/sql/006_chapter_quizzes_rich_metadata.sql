-- Add rich metadata columns to chapter_quizzes
ALTER TABLE chapter_quizzes
  ADD COLUMN IF NOT EXISTS section_index INTEGER,
  ADD COLUMN IF NOT EXISTS section_name VARCHAR,
  ADD COLUMN IF NOT EXISTS quiz_take_away TEXT,
  ADD COLUMN IF NOT EXISTS quiz_metadata JSONB;

-- Index for section-aware queries
CREATE INDEX IF NOT EXISTS idx_cq_section ON chapter_quizzes(section_index);
