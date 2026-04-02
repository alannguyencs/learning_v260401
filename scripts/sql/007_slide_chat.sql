-- Add raw_content column to lessons table
ALTER TABLE lessons ADD COLUMN IF NOT EXISTS raw_content TEXT;

-- Create slide chat messages table
CREATE TABLE IF NOT EXISTS slide_chat_messages (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL REFERENCES users(username),
    slide_identifier VARCHAR NOT NULL,
    role VARCHAR NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_slide_chat_messages_lookup
    ON slide_chat_messages (username, slide_identifier, created_at);
