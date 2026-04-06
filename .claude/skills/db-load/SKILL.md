---
name: db-load
description: Restore database from data/db/{table}.sql files on a new machine. Creates
  schema, imports data, and resets sequences. Use when user says "db load", "restore
  db", "load database", "import db", or "db restore".
---

# DB Load

Restore the database from `data/db/*.sql` files (created by `/db-compress`).

## Instructions

Run the restore script with `--schema` to create tables and import data:

```bash
python3 .claude/skills/db-compress/restore.py --project-root . --schema
```

This will:
1. Run all schema creation scripts (`scripts/sql/*.sql`) to create tables
2. Import data from `data/db/{table}.sql` in dependency order
3. Reset all SERIAL sequences to match imported data

## Prerequisites

- PostgreSQL running on the target machine
- Database created: `createdb learning_v2604`
- `.env` configured with correct `DB_URL`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`
- `data/db/` directory with exported `.sql` files (from `/db-compress`)

## Data-only restore (tables already exist)

```bash
python3 .claude/skills/db-compress/restore.py --project-root .
```
