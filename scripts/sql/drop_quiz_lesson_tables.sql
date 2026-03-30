-- Drop all quiz, lesson, and memory tables (cleanup for fresh start)
DROP TABLE IF EXISTS user_question_memories CASCADE;
DROP TABLE IF EXISTS user_lesson_memories CASCADE;
DROP TABLE IF EXISTS user_topic_memories CASCADE;
DROP TABLE IF EXISTS quiz_logs CASCADE;
DROP TABLE IF EXISTS quiz_questions CASCADE;
DROP TABLE IF EXISTS lessons CASCADE;
