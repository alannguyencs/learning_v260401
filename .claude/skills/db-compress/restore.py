#!/usr/bin/env python3
"""Restore database from data/db/{table}.sql files.

Usage:
    python3 .claude/skills/db-compress/restore.py [--project-root .]

Runs the schema creation scripts first, then imports data in dependency order.
"""

import argparse
import os
import subprocess
import sys


# Schema scripts in order
SCHEMA_SCRIPTS = [
    "scripts/sql/create_all_tables.sql",
    "scripts/sql/001_content_schema.sql",
    "scripts/sql/002_learning_progress.sql",
    "scripts/sql/003_revision_scheduling.sql",
    "scripts/sql/004_slide_skips.sql",
    "scripts/sql/005_quiz_answer_log.sql",
    "scripts/sql/007_slide_chat.sql",
]

# Tables in dependency order (parents before children)
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


def run_psql(config, sql_file):
    """Run a SQL file via psql."""
    cmd = [
        "psql",
        "-h", config["host"],
        "-U", config["user"],
        "-d", config["dbname"],
        "-f", sql_file,
        "-q",
    ]

    env = os.environ.copy()
    if config.get("password"):
        env["PGPASSWORD"] = config["password"]

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode == 0, result.stderr.strip()


def run_sql(config, sql):
    """Run a SQL string via psql -c."""
    cmd = [
        "psql",
        "-h", config["host"],
        "-U", config["user"],
        "-d", config["dbname"],
        "-c", sql,
        "-q",
    ]

    env = os.environ.copy()
    if config.get("password"):
        env["PGPASSWORD"] = config["password"]

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode == 0, result.stderr.strip()


def reset_sequences(config):
    """Reset all SERIAL sequences to match the max ID in each table."""
    # Map: (table, id_column) → sequence_name
    seq_map = [
        ("users", "id", "users_id_seq"),
        ("books", "id", "books_id_seq"),
        ("lessons", "id", "lessons_id_seq"),
        ("chapters", "id", "chapters_id_seq"),
        ("chapter_quizzes", "id", "chapter_quizzes_id_seq"),
        ("user_chapter_progress", "id", "user_chapter_progress_id_seq"),
        ("lesson_revision_rounds", "id", "lesson_revision_rounds_id_seq"),
        ("user_quiz_recall", "id", "user_quiz_recall_id_seq"),
        ("quiz_answer_log", "id", "quiz_answer_log_id_seq"),
        ("quiz_skip_log", "id", "quiz_skip_log_id_seq"),
        ("slide_chat_messages", "id", "slide_chat_messages_id_seq"),
    ]

    print("\nResetting sequences...")
    for table, col, seq in seq_map:
        sql = f"SELECT setval('{seq}', COALESCE((SELECT MAX({col}) FROM {table}), 1));"
        ok, err = run_sql(config, sql)
        status = "OK" if ok else f"FAIL: {err[:40]}"
        print(f"  {seq:<40} {status}")


def main():
    parser = argparse.ArgumentParser(description="Restore DB from data/db/*.sql files")
    parser.add_argument("--project-root", default=os.getcwd(), help="Project root directory")
    parser.add_argument("--schema", action="store_true", help="Also run schema creation scripts first")
    args = parser.parse_args()

    project_root = args.project_root
    data_dir = os.path.join(project_root, "data", "db")
    config = load_db_config(project_root)

    # Optionally run schema scripts
    if args.schema:
        print("Creating schema...")
        for script in SCHEMA_SCRIPTS:
            path = os.path.join(project_root, script)
            if os.path.exists(path):
                ok, err = run_psql(config, path)
                status = "OK" if ok else f"WARN: {err}"
                print(f"  {script}: {status}")
        print()

    # Truncate all tables (reverse dependency order) for a clean slate
    reversed_tables = list(reversed(TABLES))
    truncate_sql = f"TRUNCATE {', '.join(reversed_tables)} CASCADE;"
    print("Truncating all tables...")
    ok, err = run_sql(config, truncate_sql)
    if ok:
        print("  All tables truncated\n")
    else:
        print(f"  WARN: {err}\n")

    # Import data
    print(f"Restoring data from data/db/ → {config['dbname']}")
    print(f"{'Table':<30} {'Status':>10}")
    print("-" * 42)

    for table in TABLES:
        sql_file = os.path.join(data_dir, f"{table}.sql")
        if not os.path.exists(sql_file):
            print(f"  {table:<28} {'SKIP':>10}")
            continue

        ok, err = run_psql(config, sql_file)
        status = "OK" if ok else f"FAIL: {err[:40]}"
        print(f"  {table:<28} {status:>10}")

    # Reset sequences so next INSERT gets the right ID
    reset_sequences(config)

    # Verify row counts against expected from SQL file headers
    print("\nVerifying row counts...")
    total = 0
    mismatches = []
    for table in TABLES:
        # Get actual count from database
        cmd = ["psql", "-h", config["host"], "-U", config["user"],
               "-d", config["dbname"], "-t", "-c", f"SELECT COUNT(*) FROM {table};"]
        env = os.environ.copy()
        if config.get("password"):
            env["PGPASSWORD"] = config["password"]
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        actual = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
        total += actual

        # Get expected count from SQL file header (-- Rows: N)
        sql_file = os.path.join(data_dir, f"{table}.sql")
        expected = None
        if os.path.exists(sql_file):
            with open(sql_file) as f:
                for line in f:
                    if line.startswith("-- Rows:"):
                        try:
                            expected = int(line.split(":")[1].strip())
                        except ValueError:
                            pass
                        break

        if expected is not None and actual != expected:
            mismatches.append((table, expected, actual))
            print(f"  {table:<28} {actual:>6}  MISMATCH (expected {expected})")
        else:
            print(f"  {table:<28} {actual:>6}")

    print(f"  {'Total':<28} {total:>6}")

    if mismatches:
        print(f"\nERROR: {len(mismatches)} table(s) have row count mismatches!")
        print("The SQL files may be corrupted (multi-line content stripped).")
        print("Fix: re-export on the source machine with the latest db-compress,")
        print("     then commit and pull the updated data/db/ files.")
    else:
        print("\nRestore complete — all row counts match.")


if __name__ == "__main__":
    main()
