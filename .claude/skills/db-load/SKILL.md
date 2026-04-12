---
name: db-load
description: Restore database from data/db/{table}.sql files on a new machine. Creates
  schema, imports data, and resets sequences. Use when user says "db load", "restore
  db", "load database", "import db", or "db restore".
---

# DB Load

Restore the database from `data/db/*.sql` files (created by `/db-compress`).

## Instructions

```bash
python3 .claude/skills/db-compress/restore.py --project-root . --schema
```

This will:
1. Run all schema creation scripts (`scripts/sql/*.sql`) to create tables
2. Truncate all tables for a clean slate
3. Import data from `data/db/{table}.sql` in dependency order
4. Reset all SERIAL sequences to match imported data
5. Verify actual row counts against expected counts from SQL file headers

## If verification shows MISMATCH

Row count mismatches mean the SQL files are corrupted (usually multi-line content stripped by an old compress script). To fix:

1. Go to the **source machine** (where the data was originally exported)
2. Run `python3 .claude/skills/db-compress/compress.py --project-root .` with the latest script
3. Commit and push the updated `data/db/*.sql` files
4. Pull on this machine and run restore again

## Prerequisites

- PostgreSQL running: `brew services start postgresql` (macOS)
- Database created: `createdb learning_v2604`
- `.env` configured with `DB_URL`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`
- `data/db/` directory with exported `.sql` files

## Data-only restore (tables already exist)

```bash
python3 .claude/skills/db-compress/restore.py --project-root .
```
