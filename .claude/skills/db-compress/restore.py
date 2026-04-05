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

    print(f"\nRestore complete.")


if __name__ == "__main__":
    main()
