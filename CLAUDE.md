# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This App Is

A personal spaced-repetition learning app. A user reads short **chapters** from **lessons** inside **books**, answers **quizzes** attached to each chapter, and receives those quizzes back on a doubling-interval review schedule. The backend chooses the next slide via a 3-tier priority algorithm (due revisions → new chapters → skipped quizzes). Open-ended quiz answers are graded by an LLM (Gemini); multiple-choice is auto-graded.

## Common Commands

### Dev (runs both backend and frontend; ports come from `.env`)
```bash
./start_app.sh
```
Ports default to BACKEND_PORT=8999, FRONTEND_PORT=3999 (set in `.env`). The script kills stale processes on those ports, activates `venv/`, runs `uvicorn src.main:app --reload`, and runs `npm start` for the frontend. Logs stream to `logs/backend.log` and `logs/frontend.log`. The frontend proxies `/api`, `/auth`, `/health` to the backend via `frontend/src/setupProxy.js` (reads `BACKEND_PORT` from the root `.env`).

### Backend tests (Python / pytest, SQLite in-memory)
```bash
cd backend && dotenv -f ../.env run python -m pytest tests/ -q
# single test:
cd backend && dotenv -f ../.env run python -m pytest tests/test_slides_api.py::test_name -q
```
`backend/tests/conftest.py` swaps the real Postgres engine for SQLite `:memory:` and injects the session via `app.dependency_overrides[get_db]`. Tests MUST go through this fixture — never connect to the real DB.

### Frontend tests (Jest via react-scripts)
```bash
cd frontend && npx react-scripts test --watchAll=false
# single test:
cd frontend && npx react-scripts test --watchAll=false -t "test name"
```

### Lint / format (all enforced by pre-commit)
```bash
pre-commit run --all-files
# backend only:
cd backend && black --line-length=99 src/ && flake8 --max-line-length=99 --max-complexity=10 src/
# frontend only:
cd frontend && npx eslint "src/**/*.{js,jsx}" --fix --max-warnings=0 && npx prettier --write "src/**/*.{js,jsx,json,css}"
```
Pre-commit also runs the **full test suite** on every commit for both backend and frontend. A commit with failing tests will be rejected.

### Build (production)
```bash
cd frontend && npm run build   # outputs frontend/build/
```

### Seed local DB
```bash
python scripts/seed_local_db.py                 # seed sample lessons+quizzes into Postgres
psql -d learning_v2604 -f scripts/sql/create_all_tables.sql   # initial schema
```

## Enforced code-quality rules (pre-commit will block commits)

- **300-line cap per file** on `backend/src/**/*.py` and `frontend/src/**/*.{js,jsx}`. When a file approaches 300 lines, split it rather than working around the hook. `scripts/` is exempt.
- **No `console.log`** in `frontend/src/` (except `utils/` and `contexts/`).
- **No `debugger`** anywhere in frontend src.
- **Python**: black (99 cols), flake8 (99 cols, complexity ≤ 10), pylint with this disable set: `C0114,C0115,R0903,R0913,R0917,R1705,R0914,W0511,E0401,E1101,R0801`.
- **Frontend**: ESLint must pass with `--max-warnings=0`; Prettier applied to `.js/.jsx/.json/.css/.html`.

## Architecture

### Layered backend (`backend/src/`)
Strict four-layer FastAPI app. Dependencies flow one direction only; do not call sideways or skip layers.

```
api/          FastAPI routers. Thin — parse request, call service, return schema.
service/      Business logic. Orchestrates CRUD + LLM + cross-entity rules.
crud/         Pure DB operations (SQLAlchemy queries). No business rules.
models/       SQLAlchemy ORM classes (one file per entity cluster).
schemas/      Pydantic request/response DTOs.
```

Entry point: `src/main.py` mounts `SessionMiddleware` then `CORSMiddleware` (order matters) and includes `api.api_router` which aggregates: `auth`, `login`, `root`, `content`, `slides`, `slide_likes`, `dashboard`. All routers mount under `/api` except `auth` (`/auth`) and `login` (root).

Config: `src/configs.py` loads `.env` from project root via `pydantic-settings`. DB URL is built in `src/database.py` from `DB_USERNAME/DB_PASSWORD/DB_URL/DB_NAME` env vars (Postgres in prod, SQLite in tests). `get_db()` is the FastAPI dependency for DB sessions.

Auth: JWT (HS256, 90-day expiry) set as `HttpOnly` cookie. `authenticate_user_from_request()` reads the `access_token` cookie first, then falls back to `Authorization: Bearer <token>`. `WEBAPP_ACCESS_TOKEN` in `.env` is a long-lived token for scripts/tools.

### Core services and their responsibilities

- **`SlideSelector`** (`service/slide_selector.py`) — 3-tier algorithm that picks the next slide: **Tier 1** due revision quizzes → **Tier 2** next unlearnt chapter (book-priority or round-robin) → **Tier 3** skipped quizzes (fallback `AllCaughtUp`).
- **`slide_navigation`** (`service/slide_navigation.py`) — server-authoritative back/forward history. Pushes to `slide_history` on each forward; rebuilds `SlideResult` from stored rows on back.
- **`RevisionService`** (`service/revision_service.py`) — doubling-interval spaced repetition. `on_chapter_learnt` distributes new quizzes into R0/next-open round; `record_quiz_response` updates per-quiz recall and closes the round when all answers land. Quiz "likes" apply a forgetting-rate boost.
- **`LearningProgressService`** — marks chapters learnt, cascades to revision.
- **`QuizGrader`** (`service/quiz_grader.py`) — grades open-ended answers via Gemini (structured output).
- **`SlideChatService`** (`service/slide_chat_service.py`) — contextual Q&A on a slide, using Gemini 2.5 Flash with the lesson `raw_content` + recent chat history.

### Data model (the shape matters more than any single column)

Content hierarchy: `Book → Lesson → Chapter → ChapterQuiz`. A **chapter** is one atomic reading unit (a `## Summary`, `## Recommendation`, or `## Story` section of a lesson file). Each chapter has ~9 quizzes (1 free recall + 1 teach-back + 2 cloze + 5 MC).

Per-user state tables:
- `user_chapter_progress` — which chapters a user has learnt
- `lesson_revision_rounds` — one row per `(user, lesson_id, round_num)`, tracks due date + progress
- `user_quiz_recall` — per-quiz recall score, drives "weakest first" ordering within a round
- `quiz_answer_log`, `quiz_skip_log` — history
- `slide_position`, `slide_history` — current slide + back/forward stack (server-side)
- `user_slide_like` — polymorphic (`quiz_id` XOR `chapter_id`); quiz likes boost forgetting rate, chapter likes are bookmarks only
- `slide_chat_messages` — per-slide chat transcript (`slide_identifier` is `"chapter:{id}"` or `"quiz:{id}"`)

### Frontend (`frontend/src/`)
React 18 + react-router-dom v6 + Tailwind. Axios with `withCredentials: true` so the HttpOnly auth cookie is sent on every request.

- `App.js` — routes. `/login` is public; everything else sits under `<ProtectedRoute><AuthenticatedLayout/>`.
- `contexts/AuthContext.js` — calls `GET /api/me` on mount to restore session from cookie.
- `pages/` — `Login`, `SlidePage`, `DashboardPage`, `FavoritePage`.
- `components/` — `ChapterSlide`, `QuizSlide`, `ChatPanel`, `LikeButton`, `BookSelector`, `BottomNavBar`, etc.
- `hooks/` — `useSlide` (fetch/forward/back/mark-learnt/submit-answer), `useSlideChat`, `useLikedSlides`.
- `services/api.js` — every backend endpoint wrapped as an `apiService.*` method. Add new endpoints here, not inline in components.

### LLM integration
Gemini is the only LLM. API key is `GEMINI_API_KEY` in `.env`. System prompts live in `backend/resources/prompts/` (`quiz_grader.md`, `quiz_system_prompt.md`, `slide_chat.md`). Do not inline prompts in service files — load from `resources/prompts/`.

## Documentation conventions

Docs live under `docs/` in two mirrored levels — **abstract** (what/why, no code) and **technical** (how, with pipeline diagrams and a Component Checklist). Full rules in `docs/documentation_hierarchy.md`. When adding a feature: same filename at both levels, `Status: Plan | In Progress | Done` at the top of the abstract page, Prev/Parent/Next navigation at top and bottom of every non-index page, and a vertical-pipeline ASCII diagram under a `## Pipeline` heading on every technical page. Also add the new pipeline to `docs/technical/system_pipelines.md`.

## Data file layout (non-source)

- `data/lesson/<book_id>/<lesson>.md` — markdown lesson sources
- `data/quiz/<book_id>/<lesson>.json` — generated quiz questions for the lesson
- `data/transcript/`, `data/raw/`, `data/metadata/` — inputs for the `.claude/skills/lesson-create-*` authoring skills
- `data/db/*.sql` — table snapshots; `scripts/sql/NNN_*.sql` — ordered migrations
- `scripts/seed_local_db.py` — reads from `data/lesson` and `data/quiz` to populate a fresh local Postgres

## Gotchas

- **`SessionMiddleware` must be added before `CORSMiddleware`** in `src/main.py`. Swapping the order breaks auth in subtle ways.
- **Tests use SQLite in-memory**, production uses Postgres. Avoid Postgres-specific SQL (e.g. `JSONB` operators) in queries shared by both — prefer SQLAlchemy expressions.
- **`ALLOWED_ORIGINS` is comma-separated** and parsed in `main.py`. Multiple origins need commas with no spaces dropped.
- **Backend file caps**: if you're about to push a file past 300 lines, stop and split — the commit will fail and you'll have to redo it.
