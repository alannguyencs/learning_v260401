---
name: db-compress
description: Export all database tables to data/db/{table}.sql files for portable
  backup and restore on another computer. Use when user says "db compress", "export
  db", "backup database", "dump db", or "db snapshot".
---

# DB Compress

Export all database tables to portable SQL files in `data/db/`.

## Export (this computer → SQL files)

```bash
python3 .claude/skills/db-compress/compress.py --project-root .
```

Exports each table as INSERT statements to `data/db/{table}.sql` in dependency order.

## Restore (SQL files → another computer)

Data only (tables already exist):
```bash
python3 .claude/skills/db-compress/restore.py --project-root .
```

Full restore including schema creation:
```bash
python3 .claude/skills/db-compress/restore.py --project-root . --schema
```

## Notes

- Tables are exported/restored in dependency order (parents before children)
- SQL files use plain INSERT statements for maximum portability
- DB config is read from `.env` (`DB_URL`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`)
- `data/db/` files can be committed to git for cross-machine sync
