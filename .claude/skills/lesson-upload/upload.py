#!/usr/bin/env python3
"""Upload lesson and quiz questions to the webapp API.

Usage:
    python upload.py <base_filename> [--project-root <path>]

Accepts either:
    - bare filename:   250218_20_quantum_cheat_codes_that_i_wish_i_knew_in_my_2
    - with channel:    themitmonk/250218_20_quantum_cheat_codes_that_i_wish_i_knew_in_my_2

The script auto-discovers files across data/lesson/, data/metadata/, and data/quiz/
by searching subdirectories if the file is not found at the top level.

Upload flow:
    1. POST /api/content/books  (idempotent)
    2. POST /api/content/lessons
    3. For each section in the lesson markdown (skip Material):
         POST /api/content/chapters
         POST /api/content/quizzes  (batch per chapter)
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys


def load_env(project_root):
    """Load token and API URL from .env file."""
    env_path = os.path.join(project_root, ".env")
    if not os.path.exists(env_path):
        print("ERROR: .env file not found at", env_path)
        sys.exit(1)

    token = None
    api_url = "http://localhost:8000"

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("WEBAPP_ACCESS_TOKEN="):
                token = line.split("=", 1)[1].strip()
            elif line.startswith("WEBAPP_API_URL="):
                api_url = line.split("=", 1)[1].strip()

    if not token:
        print("ERROR: Set WEBAPP_ACCESS_TOKEN in .env first. Generate one via POST /auth/token.")
        sys.exit(1)

    return token, api_url


def find_file(project_root, data_dir, filename):
    """Find a file in data_dir, checking both flat and subdirectory layouts."""
    flat = os.path.join(project_root, data_dir, filename)
    if os.path.exists(flat):
        return flat

    pattern = os.path.join(project_root, data_dir, "*", filename)
    matches = glob.glob(pattern)
    if matches:
        return matches[0]

    return None


def read_files(project_root, base_filename):
    """Read lesson, metadata, and quiz files with auto-discovery."""
    bare = os.path.basename(base_filename)

    lesson_path = find_file(project_root, "data/lesson", f"{bare}.md")
    metadata_path = find_file(project_root, "data/metadata", f"{bare}.json")
    quiz_path = find_file(project_root, "data/quiz", f"{bare}.json")

    if not lesson_path:
        lesson_path = find_file(project_root, "data/lesson", f"{base_filename}.md")
    if not metadata_path:
        metadata_path = find_file(project_root, "data/metadata", f"{base_filename}.json")
    if not quiz_path:
        quiz_path = find_file(project_root, "data/quiz", f"{base_filename}.json")

    missing = []
    if not lesson_path:
        missing.append(f"data/lesson/**/{bare}.md")
    if not metadata_path:
        missing.append(f"data/metadata/**/{bare}.json")
    if not quiz_path:
        missing.append(f"data/quiz/**/{bare}.json")

    if missing:
        print("ERROR: Missing files:", ", ".join(missing))
        print("Run lesson-youtube or lesson-quiz-generate first.")
        sys.exit(1)

    with open(lesson_path) as f:
        lesson_content = f.read()
    with open(metadata_path) as f:
        metadata = json.load(f)
    with open(quiz_path) as f:
        questions = json.load(f)

    metadata["_lesson_path"] = lesson_path
    return lesson_content, metadata, questions


def parse_lesson_sections(lesson_content):
    """Split lesson markdown into sections. Skip 'Material' (section 0).

    Returns list of {section_index, title, content} dicts.
    """
    parts = re.split(r"\n---\n", lesson_content)
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
        content_lines = [ln for ln in lines if ln != heading_line]
        content = "\n".join(content_lines).strip()
        sections.append({"section_index": index, "title": title, "content": content})
    return sections


def _post_json(api_url, token, path, payload, tmp_file):
    """POST JSON payload to the API. Returns parsed response dict."""
    with open(tmp_file, "w") as f:
        json.dump(payload, f)

    result = subprocess.run(
        [
            "curl",
            "-s",
            "--connect-timeout",
            "10",
            "--max-time",
            "30",
            "-X",
            "POST",
            f"{api_url}/api/{path}",
            "-H",
            f"Authorization: Bearer {token}",
            "-H",
            "Content-Type: application/json",
            "-d",
            f"@{tmp_file}",
        ],
        capture_output=True,
        text=True,
    )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"_raw": result.stdout}


def upload_book(api_url, token, book_id, book_title):
    """POST /api/content/books. Ignore 409 (book already exists)."""
    data = _post_json(
        api_url, token, "content/books", {"book_id": book_id, "title": book_title}, "/tmp/book_upload.json"
    )
    if "id" in data:
        print(f"Book: \"{book_title}\" (ID: {data['id']})")
    elif "already exists" in str(data).lower() or "409" in str(data):
        print(f"Book: \"{book_title}\" (already exists)")
    else:
        print(f"ERROR creating book: {data}")
        sys.exit(1)


def upload_lesson_record(api_url, token, book_id, lesson_index, title, raw_content=None):
    """POST /api/content/lessons. Returns lesson_id."""
    payload = {"book_id": book_id, "lesson_index": lesson_index, "title": title}
    if raw_content:
        payload["raw_content"] = raw_content
    data = _post_json(
        api_url,
        token,
        "content/lessons",
        payload,
        "/tmp/lesson_upload.json",
    )
    if "id" in data:
        print(f"Lesson: \"{title}\" (ID: {data['id']}, index: {lesson_index})")
        return data["id"]
    print(f"ERROR uploading lesson: {data}")
    sys.exit(1)


def upload_chapter(api_url, token, lesson_id, section):
    """POST /api/content/chapters. Returns chapter_id."""
    data = _post_json(
        api_url,
        token,
        "content/chapters",
        {
            "lesson_id": lesson_id,
            "chapter_index": section["section_index"],
            "title": section["title"],
            "content": section["content"],
        },
        "/tmp/chapter_upload.json",
    )
    if "id" in data:
        return data["id"]
    print(f"ERROR uploading chapter '{section['title']}': {data}")
    sys.exit(1)


def map_quiz_to_create(q, section_index, section_name):
    """Map a quiz JSON object from lesson-quiz-generate to a QuizCreate payload."""
    quiz_format = q.get("quiz_format", "")

    quiz_type = "cloze" if quiz_format == "cloze_deletion" else quiz_format

    if quiz_format == "cloze_deletion":
        question = q.get("sentence", "")
        expected_answer = ", ".join(q.get("blanks", []))
        quiz_metadata = {
            "blanks": q.get("blanks", []),
            "context_hint": q.get("context_hint", ""),
        }
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
        "correct_options": q.get("correct_options"),
        "section_index": section_index,
        "section_name": section_name,
        "quiz_take_away": q.get("quiz_take_away"),
        "quiz_metadata": quiz_metadata,
    }


def upload_chapter_quizzes(api_url, token, chapter_id, quiz_batch):
    """POST /api/content/quizzes batch for a chapter. Returns count inserted."""
    data = _post_json(
        api_url,
        token,
        "content/quizzes",
        {"chapter_id": chapter_id, "quizzes": quiz_batch},
        "/tmp/quiz_upload.json",
    )
    if "inserted" in data:
        return data["inserted"]
    print(f"ERROR uploading quizzes for chapter {chapter_id}: {data}")
    sys.exit(1)


def tick_to_learn(project_root, base_filename):
    """Mark lesson as done in to_learn.md."""
    to_learn_path = os.path.join(project_root, "data/to_learn.md")
    if not os.path.exists(to_learn_path):
        return

    bare = os.path.basename(base_filename)

    with open(to_learn_path) as f:
        content = f.read()

    if bare not in content:
        return

    lines = content.split("\n")
    new_lines = []
    for line in lines:
        if bare in line and line.strip().startswith("- [ ]"):
            line = line.replace("- [ ]", "- [x]", 1)
        new_lines.append(line)

    with open(to_learn_path, "w") as f:
        f.write("\n".join(new_lines))
    print("Checked off in data/to_learn.md")


def cleanup():
    """Remove temp files."""
    for path in [
        "/tmp/book_upload.json",
        "/tmp/lesson_upload.json",
        "/tmp/chapter_upload.json",
        "/tmp/quiz_upload.json",
    ]:
        if os.path.exists(path):
            os.remove(path)


def main():
    parser = argparse.ArgumentParser(description="Upload lesson and quiz questions to API")
    parser.add_argument(
        "base_filename",
        help="Base filename without extension (e.g. '250218_my_lesson' or 'themitmonk/250218_my_lesson')",
    )
    parser.add_argument("--project-root", default=os.getcwd(), help="Project root directory")
    args = parser.parse_args()

    project_root = args.project_root
    base_filename = args.base_filename

    # Step 1: Load token and read files
    token, api_url = load_env(project_root)
    lesson_content, metadata, questions = read_files(project_root, base_filename)

    # Step 2: Derive book_id and lesson_index
    channel = metadata["channel"]
    book_id = re.sub(r"\s+", "_", channel.lower())
    book_id = re.sub(r"[^a-z0-9_]", "", book_id)
    book_title = channel
    lesson_index = int(metadata["published_date"].replace("-", ""))
    lesson_title = metadata["title"]

    # Step 3: Upload book (idempotent)
    upload_book(api_url, token, book_id, book_title)

    # Step 4: Upload lesson record (include transcript as raw_content)
    raw_content = metadata.get("transcript")
    lesson_id = upload_lesson_record(api_url, token, book_id, lesson_index, lesson_title, raw_content)

    # Step 5: Parse lesson sections
    sections = parse_lesson_sections(lesson_content)
    if not sections:
        print("ERROR: No sections found in lesson markdown.")
        sys.exit(1)
    print(f"Sections found: {[s['title'] for s in sections]}")

    # Step 6: Group quizzes by section_index
    quizzes_by_section = {}
    for q in questions:
        si = int(q.get("section", 0))
        quizzes_by_section.setdefault(si, []).append(q)

    # Step 7: Upload chapters + quizzes
    total_quizzes = 0
    for section in sections:
        si = section["section_index"]
        chapter_id = upload_chapter(api_url, token, lesson_id, section)

        section_quizzes = quizzes_by_section.get(si, [])
        if not section_quizzes:
            print(f"  Section {si} ({section['title']}): chapter uploaded, no quizzes found")
            continue

        quiz_batch = [map_quiz_to_create(q, si, section["title"]) for q in section_quizzes]
        inserted = upload_chapter_quizzes(api_url, token, chapter_id, quiz_batch)
        total_quizzes += inserted
        print(f"  Section {si} ({section['title']}): chapter {chapter_id}, {inserted} quizzes")

    # Step 8: Tick to-learn
    tick_to_learn(project_root, base_filename)

    # Cleanup
    cleanup()

    print(f"\nResult: Lesson ID {lesson_id} ({book_title}), {total_quizzes} quizzes uploaded")


if __name__ == "__main__":
    main()
