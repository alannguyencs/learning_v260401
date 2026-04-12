---
name: db-compress
description: Export all database tables to data/db/{table}.sql files for portable
  backup and restore on another computer. Use when user says "db compress", "export
  db", "backup database", "dump db", or "db snapshot".
---

# DB Compress

Export all database tables to portable SQL files in `data/db/`.

## Export

```bash
python3 .claude/skills/db-compress/compress.py --project-root .
```

- Exports each table as INSERT statements to `data/db/{table}.sql`
- Handles multi-line content (lesson text, quiz JSON) correctly
- Verifies all exported SQL files are valid
- Each file has a `-- Rows: N` header for restore verification

## After exporting

Commit the updated `data/db/*.sql` files to git so they sync to the other machine.

## Important

The Activity Log dashboard has no dedicated table — it is a UNION ALL view of 4 tables:
- `user_chapter_progress` (LEARNT CHAPTER events)
- `quiz_skip_log` (SKIP events)
- `quiz_answer_log` (ANSWER events)
- `lesson_revision_rounds` (ROUND CREATED events)

All 4 tables are exported by db-compress. As long as the export is done **after** studying (answering quizzes, learning chapters), the activity log will be preserved when restored on another machine.
