#!/usr/bin/env python3
"""Export each database table to data/db/{table}.sql as INSERT statements.

Usage:
    python3 .claude/skills/db-compress/compress.py [--project-root .]

Creates portable SQL files that can restore the database on another machine:
    psql -h 127.0.0.1 -d learning_v2604 -f data/db/{table}.sql
"""

import argparse
import os
import subprocess
import sys


# Tables in dependency order (parents before children).
TABLES = [
    "users",
    "books",
    "lessons",
    "chapters",
    "chapter_quizzes",
    "user_chapter_progress",
    "user_lesson_count",
    "lesson_revision_rounds",
    "user_quiz_recall",
    "quiz_answer_log",
    "quiz_skip_log",
    "slide_chat_messages",
]


def load_db_config(project_root):
    """Load DB connection info from .env."""
    env_path = os.path.join(project_root, ".env")
    if not os.path.exists(env_path):
        print("ERROR: .env not found at", env_path)
        sys.exit(1)

    config = {"host": "127.0.0.1", "dbname": "learning_v2604", "user": "alan"}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("DB_URL="):
                config["host"] = line.split("=", 1)[1].strip()
            elif line.startswith("DB_NAME="):
                config["dbname"] = line.split("=", 1)[1].strip()
            elif line.startswith("DB_USERNAME="):
                config["user"] = line.split("=", 1)[1].strip()
            elif line.startswith("DB_PASSWORD="):
                config["password"] = line.split("=", 1)[1].strip()
    return config


def dump_table(config, table, output_path):
    """Dump a single table to a SQL file using pg_dump --inserts."""
    cmd = [
        "pg_dump",
        "-h", config["host"],
        "-U", config["user"],
        "-d", config["dbname"],
        "--table", table,
        "--data-only",
        "--inserts",
        "--no-owner",
        "--no-privileges",
        "--on-conflict-do-nothing",
    ]

    env = os.environ.copy()
    if config.get("password"):
        env["PGPASSWORD"] = config["password"]

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)

    if result.returncode != 0:
        print(f"  ERROR dumping {table}: {result.stderr.strip()}")
        return 0

    # Extract complete INSERT statements (may span multiple lines).
    # Each statement starts with "INSERT INTO" and ends with ");" on some line.
    statements = []
    current = []
    in_insert = False
    for line in result.stdout.splitlines():
        if line.startswith("INSERT INTO"):
            current = [line]
            in_insert = True
        elif in_insert:
            current.append(line)
        if in_insert and line.rstrip().endswith(";"):
            statements.append("\n".join(current))
            current = []
            in_insert = False

    row_count = len(statements)
    lines = statements

    with open(output_path, "w") as f:
        f.write(f"-- Table: {table}\n")
        f.write(f"-- Rows: {row_count}\n")
        f.write(f"-- Export tool: db-compress\n\n")
        if lines:
            f.write("\n".join(lines))
            f.write("\n")

    return row_count


def main():
    parser = argparse.ArgumentParser(description="Export DB tables to data/db/*.sql")
    parser.add_argument("--project-root", default=os.getcwd(), help="Project root directory")
    args = parser.parse_args()

    project_root = args.project_root
    output_dir = os.path.join(project_root, "data", "db")
    os.makedirs(output_dir, exist_ok=True)

    config = load_db_config(project_root)

    print(f"Exporting {config['dbname']} → data/db/")
    print(f"{'Table':<30} {'Rows':>6}")
    print("-" * 38)

    total_rows = 0
    total_tables = 0

    for table in TABLES:
        output_path = os.path.join(output_dir, f"{table}.sql")
        rows = dump_table(config, table, output_path)
        total_rows += rows
        total_tables += 1
        print(f"  {table:<28} {rows:>6}")

    print("-" * 38)
    print(f"  {'Total':<28} {total_rows:>6}")
    print(f"\n{total_tables} tables exported to data/db/")

    # Verify: each INSERT statement must end with a line containing ');'
    errors = []
    for table in TABLES:
        sql_file = os.path.join(output_dir, f"{table}.sql")
        if not os.path.exists(sql_file):
            continue
        with open(sql_file) as f:
            content = f.read()
        for stmt in content.split("INSERT INTO")[1:]:  # skip header before first INSERT
            # The last non-empty line of each statement must end with ';'
            stmt_lines = [l for l in stmt.strip().splitlines() if l.strip()]
            if stmt_lines and not stmt_lines[-1].rstrip().endswith(";"):
                errors.append(table)
                break
    if errors:
        print(f"\nWARNING: Potentially broken SQL in: {', '.join(errors)}")
        print("Multi-line content may not have exported correctly.")
    else:
        print("Verification: all SQL files OK")


if __name__ == "__main__":
    main()
