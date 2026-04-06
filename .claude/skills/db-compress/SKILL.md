---
name: db-compress
description: Export all database tables to data/db/{table}.sql files for portable
  backup and restore on another computer. Use when user says "db compress", "export
  db", "backup database", "dump db", or "db snapshot".
---

# DB Compress

Export all database tables to portable SQL files in `data/db/`.

## Export (this computer -> SQL files)

```bash
python3 .claude/skills/db-compress/compress.py --project-root .
```

Exports each table as INSERT statements to `data/db/{table}.sql` in dependency order.
Handles multi-line content (lesson text, quiz JSON) correctly.
Verifies all exported SQL files are valid at the end.

## After exporting

Commit the updated `data/db/*.sql` files to git so they can be restored on another machine.
