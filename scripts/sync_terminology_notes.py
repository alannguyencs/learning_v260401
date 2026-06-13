#!/usr/bin/env python3
"""Sync terminologies/notes/*.md into the terminology_notes Postgres table.

For every note it computes the BM25 stats (token length + term frequencies),
parses the title and the "### Key terminologies" term names, and upserts a row.
Rows whose source file no longer exists are pruned, so the table always mirrors
the folder. Run on deploy and after editing notes.

Usage:
    python scripts/sync_terminology_notes.py
    python scripts/sync_terminology_notes.py --dry-run

Requires the backend DB env vars (DB_USERNAME / DB_NAME / DB_URL / DB_PASSWORD);
loaded from the project-root .env if python-dotenv is installed.
"""

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NOTES_DIR = PROJECT_ROOT / "terminologies" / "notes"

# Make the backend package importable and load .env so SessionLocal can connect.
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from src.crud import crud_terminology_notes as crud  # noqa: E402
from src.database import SessionLocal  # noqa: E402
from src.utils import bm25_core  # noqa: E402

HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$")
TERM_BULLET_RE = re.compile(r"^\s*[-*]\s+\*\*(.+?)\*\*\s*(?:[—–:-]\s*)?(.*)$")
KEY_TERMS_HEADING = "key terminologies"


def parse_note(text: str):
    """Return (title, [term names]) for a note's markdown body."""
    title = ""
    terms = []
    seen = set()
    in_section = False
    for line in text.splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            if not title:
                title = heading.group(1).strip()
            in_section = heading.group(1).strip().lower() == KEY_TERMS_HEADING
            continue
        if not in_section:
            continue
        m = TERM_BULLET_RE.match(line)
        if m:
            term = m.group(1).strip()
            if term and term not in seen:
                seen.add(term)
                terms.append(term)
    return title or "(untitled)", terms


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Sync notes into terminology_notes.")
    parser.add_argument("--dry-run", action="store_true", help="report changes without writing")
    args = parser.parse_args(argv)

    files = sorted(NOTES_DIR.glob("*.md"))
    seen_paths = set()
    db = SessionLocal()
    try:
        for path in files:
            rel_path = path.relative_to(PROJECT_ROOT).as_posix()
            seen_paths.add(rel_path)
            text = path.read_text(encoding="utf-8")
            tokens = bm25_core.tokenize(text)
            if not tokens:
                print(f"  skip (no tokens): {rel_path}")
                continue
            title, terms = parse_note(text)
            if args.dry_run:
                print(f"  would upsert: {rel_path} ({len(tokens)} tokens, {len(terms)} terms)")
                continue
            crud.upsert(
                db,
                rel_path=rel_path,
                title=title,
                raw_content=text,
                terminologies=terms,
                token_length=len(tokens),
                term_freq=bm25_core.term_freq(tokens),
            )
            print(f"  upserted: {rel_path} ({len(tokens)} tokens, {len(terms)} terms)")

        pruned = 0
        for row in crud.list_all(db):
            if row.rel_path not in seen_paths:
                if args.dry_run:
                    print(f"  would prune: {row.rel_path}")
                else:
                    crud.delete_by_rel_path(db, row.rel_path)
                    print(f"  pruned: {row.rel_path}")
                pruned += 1
    finally:
        db.close()

    verb = "Would sync" if args.dry_run else "Synced"
    print(f"{verb} {len(files)} note(s); {pruned} stale row(s).")


if __name__ == "__main__":
    main()
