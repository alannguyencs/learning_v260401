#!/usr/bin/env python3
"""Seed local database with lesson and quiz data directly (no API required).

Usage:
    python scripts/seed_local_db.py
"""

import json
import os
import re
import sys
from pathlib import Path

import psycopg2

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── Config ──────────────────────────────────────────────────────────
DB_NAME = "learning_v2604"
DB_USER = "alan"
DB_HOST = "127.0.0.1"
DB_PORT = 5432

# ── Files to seed ───────────────────────────────────────────────────
SEEDS = [
    {
        "book_id": "coach",
        "book_title": "coach",
        "lesson_index": 20260324,
        "lesson_title": "Frequent Time-Framed Learning & Coaching: Science-Backed Strategies for Efficient Knowledge Acquisition and Long-Term Retention",
        "lesson_path": PROJECT_ROOT / "data/lesson/coach/260324_time_framed_learning.md",
        "quiz_path": PROJECT_ROOT / "data/quiz/260324_time_framed_learning.json",
        "section_separator": r"\n(?=## )",
    },
    {
        "book_id": "themitmonk",
        "book_title": "theMITmonk",
        "lesson_index": 20250218,
        "lesson_title": "20 Quantum Cheat Codes That I Wish I Knew In My 20's",
        "lesson_path": PROJECT_ROOT / "data/lesson/themitmonk/250218_20_quantum_cheat_codes_that_i_wish_i_knew_in_my_2.md",
        "quiz_path": PROJECT_ROOT / "data/quiz/themitmonk/250218_20_quantum_cheat_codes_that_i_wish_i_knew_in_my_2.json",
        "section_separator": r"\n---\n",
    },
    {
        "book_id": "themitmonk",
        "book_title": "theMITmonk",
        "lesson_index": 20250228,
        "lesson_title": "From Homeless to MIT Grad: How I Started from $0 and Created Billions",
        "lesson_path": PROJECT_ROOT / "data/lesson/themitmonk/250228_from_homeless_to_mit_grad_how_i_started_from_0_an.md",
        "quiz_path": PROJECT_ROOT / "data/quiz/themitmonk/250228_from_homeless_to_mit_grad_how_i_started_from_0_an.json",
        "section_separator": r"\n---\n",
    },
    {
        "book_id": "learning_phrases_with_chris_friends",
        "book_title": "Learning Phrases with Chris & Friends",
        "lesson_index": 20211118,
        "lesson_title": "Useful English Cartoons: My Room - Basic English Vocabulary with Subtitles",
        "lesson_path": PROJECT_ROOT / "data/lesson/learning_phrases_with_chris_friends/211118_useful_english_cartoons_my_room_basic_english_vocab.md",
        "quiz_path": PROJECT_ROOT / "data/quiz/learning_phrases_with_chris_friends/211118_useful_english_cartoons_my_room_basic_english_vocab.json",
        "section_separator": r"\n---\n",
    },
]


def parse_sections(lesson_content, separator):
    """Split lesson markdown into sections. Skip 'Material' (section 0)."""
    parts = re.split(separator, lesson_content)
    sections = []
    index = 0
    for part in parts:
        lines = part.strip().split("\n")
        if not lines:
            continue
        heading_line = next((ln for ln in lines if ln.startswith("## ")), None)
        if not heading_line:
            continue
        title = heading_line[3:].strip()
        if title.lower() == "material":
            continue
        index += 1
        sections.append({"section_index": index, "title": title, "content": part.strip()})
    return sections


def map_quiz(q, section_index, section_name):
    """Map a quiz JSON object to DB columns."""
    quiz_format = q.get("quiz_format", "")
    quiz_type = "cloze" if quiz_format == "cloze_deletion" else quiz_format

    if quiz_format == "cloze_deletion":
        question = q.get("sentence", "")
        expected_answer = ", ".join(q.get("blanks", []))
        quiz_metadata = {"blanks": q.get("blanks", []), "context_hint": q.get("context_hint", "")}
    elif quiz_format == "free_recall":
        question = q.get("question", "")
        expected_answer = q.get("model_answer")
        quiz_metadata = {"key_points": q.get("key_points", [])}
    elif quiz_format == "teach_back":
        question = q.get("question", "")
        expected_answer = q.get("model_answer")
        quiz_metadata = {"key_elements": q.get("key_elements", [])}
    elif quiz_format == "multiple_choice":
        question = q.get("question", "")
        expected_answer = None
        quiz_metadata = {
            "quiz_type_cognitive": q.get("quiz_type", ""),
            "quiz_learnt": q.get("quiz_learnt", ""),
            "response_to_user_option_a": q.get("response_to_user_option_a", ""),
            "response_to_user_option_b": q.get("response_to_user_option_b", ""),
            "response_to_user_option_c": q.get("response_to_user_option_c", ""),
            "response_to_user_option_d": q.get("response_to_user_option_d", ""),
        }
    else:
        question = q.get("question", "")
        expected_answer = q.get("model_answer")
        quiz_metadata = {}

    return {
        "quiz_type": quiz_type,
        "question": question,
        "expected_answer": expected_answer,
        "option_a": q.get("option_a"),
        "option_b": q.get("option_b"),
        "option_c": q.get("option_c"),
        "option_d": q.get("option_d"),
        "correct_options": json.dumps(q.get("correct_options")) if q.get("correct_options") else None,
        "section_index": section_index,
        "section_name": section_name,
        "quiz_take_away": q.get("quiz_take_away"),
        "quiz_metadata": json.dumps(quiz_metadata) if quiz_metadata else None,
    }


def main():
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, host=DB_HOST, port=DB_PORT)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        for seed in SEEDS:
            # 1. Upsert book
            cur.execute(
                "INSERT INTO books (book_id, title) VALUES (%s, %s) ON CONFLICT (book_id) DO NOTHING RETURNING id",
                (seed["book_id"], seed["book_title"]),
            )
            row = cur.fetchone()
            if row:
                print(f"Book: '{seed['book_title']}' (ID: {row[0]})")
            else:
                print(f"Book: '{seed['book_title']}' (already exists)")

            # 2. Insert lesson (skip if already exists)
            cur.execute(
                "SELECT id FROM lessons WHERE book_id = %s AND lesson_index = %s",
                (seed["book_id"], seed["lesson_index"]),
            )
            existing = cur.fetchone()
            if existing:
                print(f"Lesson: '{seed['lesson_title']}' (already exists, skipping)")
                continue
            cur.execute(
                "INSERT INTO lessons (book_id, lesson_index, title) VALUES (%s, %s, %s) RETURNING id",
                (seed["book_id"], seed["lesson_index"], seed["lesson_title"]),
            )
            lesson_id = cur.fetchone()[0]
            print(f"Lesson: '{seed['lesson_title']}' (ID: {lesson_id})")

            # 3. Parse sections
            lesson_content = seed["lesson_path"].read_text()
            sections = parse_sections(lesson_content, seed["section_separator"])
            print(f"  Sections: {[s['title'] for s in sections]}")

            # 4. Load quizzes grouped by section
            quizzes_by_section = {}
            if seed["quiz_path"]:
                questions = json.loads(seed["quiz_path"].read_text())
                for q in questions:
                    si = int(q.get("section", 0))
                    quizzes_by_section.setdefault(si, []).append(q)

            # 5. Insert chapters + quizzes
            total_quizzes = 0
            for section in sections:
                si = section["section_index"]
                cur.execute(
                    "INSERT INTO chapters (lesson_id, chapter_index, title, content) VALUES (%s, %s, %s, %s) RETURNING id",
                    (lesson_id, si, section["title"], section["content"]),
                )
                chapter_id = cur.fetchone()[0]

                section_quizzes = quizzes_by_section.get(si, [])
                for q in section_quizzes:
                    mapped = map_quiz(q, si, section["title"])
                    cur.execute(
                        """INSERT INTO chapter_quizzes
                           (chapter_id, quiz_type, question, expected_answer,
                            option_a, option_b, option_c, option_d, correct_options,
                            section_index, section_name, quiz_take_away, quiz_metadata)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (
                            chapter_id,
                            mapped["quiz_type"],
                            mapped["question"],
                            mapped["expected_answer"],
                            mapped["option_a"],
                            mapped["option_b"],
                            mapped["option_c"],
                            mapped["option_d"],
                            mapped["correct_options"],
                            mapped["section_index"],
                            mapped["section_name"],
                            mapped["quiz_take_away"],
                            mapped["quiz_metadata"],
                        ),
                    )
                    total_quizzes += 1

                quiz_info = f", {len(section_quizzes)} quizzes" if section_quizzes else ""
                print(f"  Chapter {si} '{section['title']}' (ID: {chapter_id}){quiz_info}")

            print(f"  Total quizzes: {total_quizzes}\n")

        conn.commit()
        print("Seed complete.")

    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
