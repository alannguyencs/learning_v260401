# Remove Quiz & Recall Dashboard

**Feature**: Remove all quiz, recall dashboard, and lesson files so the features can be rebuilt from scratch
**Plan Created:** 2026-03-30
**Status:** Plan
**Reference**:
- [Abstract — Quiz](../abstract/quiz.md)
- [Abstract — Recall Dashboard](../abstract/recall_dashboard.md)
- [Technical — Quiz](../technical/quiz.md)
- [Technical — Recall Dashboard](../technical/recall_dashboard.md)

---

## Problem Statement

1. The quiz and recall dashboard features were designed and partially implemented. The developer wants to start over with a clean design.
2. Multiple incremental plan files accumulated across `docs/plan/` that are now obsolete.
3. The existing codebase has quiz/lesson/recall code tightly spread across backend models, CRUD, services, API, schemas, and frontend pages/components/hooks/tests — all of which must be removed cleanly.
4. Authentication must be fully preserved and remain functional after the cleanup.

---

## Proposed Solution

Delete all files that belong exclusively to the quiz, recall dashboard, and lesson features. Update the files that are shared with authentication (api_router, models/__init__, main.py, App.js, api.js) to remove quiz/lesson/recall references. Update all documentation index files and navigation links. Add a SQL drop-tables migration for the removed database tables.

---

## Current Implementation Analysis

### What Exists (keep as-is)

| Component | File | Status |
|-----------|------|--------|
| Users model | `backend/src/models/user.py` | Keep — auth |
| Auth schemas | `backend/src/schemas/auth.py` | Keep — auth |
| Auth API | `backend/src/api/auth.py` | Keep — auth |
| Login API | `backend/src/api/login.py` | Keep — auth |
| User CRUD | `backend/src/crud/crud_user.py` | Keep — auth |
| Database setup | `backend/src/database.py` | Keep — infra |
| Config | `backend/src/configs.py` | Keep — infra |
| Login page | `frontend/src/pages/Login.jsx` | Keep — auth |
| AuthContext | `frontend/src/contexts/AuthContext.js` | Keep — auth |
| ProtectedRoute | `frontend/src/components/ProtectedRoute.jsx` | Keep — auth |
| Auth tests | `frontend/src/__tests__/contexts/AuthContext.test.js` | Keep — auth |
| Auth tests | `frontend/src/__tests__/components/ProtectedRoute.test.js` | Keep — auth |
| Auth tests | `frontend/src/__tests__/components/Login.test.js` | Keep — auth |
| Abstract auth doc | `docs/abstract/authentication.md` | Keep (update nav only) |
| Technical auth doc | `docs/technical/authentication.md` | Keep (update nav only) |
| System pipelines doc | `docs/technical/system_pipelines.md` | Keep (remove quiz/recall sections) |

### What Changes

| Component | Current | Proposed |
|-----------|---------|----------|
| `backend/src/models/__init__.py` | Imports 7 models including quiz/lesson | Import only `Users` |
| `backend/src/api/api_router.py` | Includes quiz, recall_dashboard, lesson routers | Include only auth, login, root |
| `backend/src/main.py` | Calls `sync_from_db` from topic_lookup in lifespan | Remove lifespan hook entirely |
| `frontend/src/App.js` | Routes for quiz, dashboard, recall, lessons | Routes for login only; redirect `/` to `/login` |
| `frontend/src/services/api.js` | Auth + quiz + lesson + recall methods | Auth methods only (login, logout, getCurrentUser) |
| `docs/abstract/index.md` | 3 rows: Auth, Quiz, Recall Dashboard | 1 row: Auth |
| `docs/technical/index.md` | 4 rows: System Pipelines, Auth, Quiz, Recall Dashboard | 2 rows: System Pipelines, Auth |
| `docs/technical/system_pipelines.md` | 7 pipelines including quiz/recall | 2 pipelines: Login, Session Restore |
| `docs/abstract/authentication.md` | Footer nav: `Next: Quiz >` | Footer nav: omit Next (last page) |
| `docs/technical/authentication.md` | Footer nav: `Next: Quiz >` | Footer nav: omit Next (last page) |
| `docs/checklist.md` | 5 implementation entries + 5 DB migration entries | Clear all quiz/lesson plan entries |

---

## Implementation Plan

### Key Workflow

This is a deletion task. No new workflows are introduced. After completion:

```
User opens app
  │
  ▼
App.js renders Router
  │
  ▼
/ → ProtectedRoute → redirect to /login (if not authenticated)
  │
  ▼
/login → Login page
  │
  ▼
Successful login → redirect to / (which redirects to /login if no other page)
```

Note: After cleanup, the app will only serve the login page. A new home page must be planned separately.

### Database Schema

#### To Delete
Remove the following SQL migration scripts (all superseded by the drop migration below):
- `scripts/sql/add_lessons_table.sql`
- `scripts/sql/add_topic_lesson_names.sql`
- `scripts/sql/add_topic_name_to_lessons.sql`
- `scripts/sql/add_question_memory.sql`

Update (do not delete — contains users table):
- `scripts/sql/create_all_tables.sql` — remove all non-auth table DDL; keep only the `users` table definition.

Delete (quiz cloud-prep script, no longer applicable):
- `scripts/sql/prepare_cloud_for_upload.sql`

#### To Update
None.

#### To Add New
New migration file: `scripts/sql/drop_quiz_lesson_tables.sql`

```sql
-- Drop all quiz, lesson, and memory tables (cleanup for fresh start)
DROP TABLE IF EXISTS user_question_memories CASCADE;
DROP TABLE IF EXISTS user_lesson_memories CASCADE;
DROP TABLE IF EXISTS user_topic_memories CASCADE;
DROP TABLE IF EXISTS quiz_logs CASCADE;
DROP TABLE IF EXISTS quiz_questions CASCADE;
DROP TABLE IF EXISTS lessons CASCADE;
```

### CRUD

#### To Delete
| File | Reason |
|------|--------|
| `backend/src/crud/crud_quiz_log.py` | QuizLog CRUD — quiz only |
| `backend/src/crud/crud_quiz_question.py` | QuizQuestion CRUD — quiz only |
| `backend/src/crud/crud_topic_memory.py` | UserTopicMemory CRUD — quiz only |
| `backend/src/crud/crud_lesson_memory.py` | UserLessonMemory CRUD — quiz only |
| `backend/src/crud/crud_question_memory.py` | UserQuestionMemory CRUD — quiz only |
| `backend/src/crud/crud_lesson.py` | Lesson CRUD — quiz only |

#### To Update
- `backend/src/crud/__init__.py` — remove any quiz/lesson imports if present.

#### To Add New
None.

### Services

#### To Delete
| File | Reason |
|------|--------|
| `backend/src/service/quiz_selector.py` | Quiz selection logic |
| `backend/src/service/answer_service.py` | Answer grading logic |
| `backend/src/service/memory_service.py` | MEMORIZE memory update logic |
| `backend/src/service/recall_service.py` | Recall dashboard service |
| `backend/src/service/topic_lookup.py` | Topic in-memory cache (quiz-specific) |

#### To Update
- `backend/src/main.py`:
  - Remove `from src.service.topic_lookup import sync_from_db`
  - Remove the entire `@asynccontextmanager async def lifespan(app)` function and `lifespan=lifespan` from the `FastAPI(...)` constructor. The app no longer needs startup hooks.

#### To Add New
None.

### API Endpoints

#### To Delete
| File | Routes removed |
|------|---------------|
| `backend/src/api/quiz.py` | All `/api/quiz/*` endpoints |
| `backend/src/api/recall_dashboard.py` | `/api/quiz/recall-map`, `/api/quiz/topic-matrix` |
| `backend/src/api/lesson.py` | `/api/lessons/*` endpoints |

#### To Update
- `backend/src/api/api_router.py`:
  - Remove imports: `lesson`, `recall_dashboard`, `quiz`
  - Remove `api_router.include_router(quiz.router, ...)`, `api_router.include_router(recall_dashboard.router, ...)`, `api_router.include_router(lesson.router, ...)`
  - Keep: `auth`, `login`, `root`

#### To Add New
None.

### Testing

#### To Delete
| File | Reason |
|------|--------|
| `frontend/src/__tests__/components/RecallHeatmap.test.js` | Recall dashboard component |
| `frontend/src/__tests__/components/TopicMatrix.test.js` | Recall dashboard component |
| `frontend/src/__tests__/components/TopicLessonFilter.test.js` | Quiz component |
| `frontend/src/__tests__/hooks/useDashboardData.test.js` | Recall dashboard hook |
| `frontend/src/__tests__/components/QuizResult.test.js` | Quiz component |
| `frontend/src/__tests__/components/QuizCard.test.js` | Quiz component |
| `frontend/src/__tests__/hooks/useQuiz.test.js` | Quiz hook |
| `frontend/src/__tests__/components/LoopSummary.test.js` | Quiz component |
| `frontend/src/__tests__/components/QuizLaunchButton.test.js` | Quiz component |
| `frontend/src/__tests__/components/RecallSummary.test.js` | Recall dashboard component |

#### To Update
None.

#### To Add New
None.

After all deletions and updates:

1. Run `source venv/bin/activate && pre-commit run --all-files`.
2. Fix any issues (e.g., lint errors, unused imports, missing module errors from deleted files).
3. Re-run pre-commit again — Prettier may reformat files. Fix any line-count violations.
4. Repeat until pre-commit passes cleanly on a full re-run with no new failures.

### Frontend

#### To Delete

**Pages:**
| File | Reason |
|------|--------|
| `frontend/src/pages/QuizPage.jsx` | Quiz page |
| `frontend/src/pages/RecallDashboardPage.jsx` | Recall dashboard page |
| `frontend/src/pages/LessonDashboardPage.jsx` | Lesson table page |
| `frontend/src/pages/LessonDetailPage.jsx` | Lesson detail page |

**Components:**
| File | Reason |
|------|--------|
| `frontend/src/components/TopicMatrix.jsx` | Recall dashboard |
| `frontend/src/components/LessonRecallList.jsx` | Recall dashboard |
| `frontend/src/components/RecallHeatmap.jsx` | Recall dashboard |
| `frontend/src/components/QuizLaunchButton.jsx` | Quiz |
| `frontend/src/components/RecallSummary.jsx` | Recall dashboard |
| `frontend/src/components/QuizResult.jsx` | Quiz |
| `frontend/src/components/TopicLessonFilter.jsx` | Quiz |
| `frontend/src/components/QuizCard.jsx` | Quiz |
| `frontend/src/components/LoopSummary.jsx` | Quiz |
| `frontend/src/components/MarkdownPreview.jsx` | Lesson detail |

**Hooks:**
| File | Reason |
|------|--------|
| `frontend/src/hooks/useDashboardData.js` | Recall dashboard hook |
| `frontend/src/hooks/useQuiz.js` | Quiz hook |

#### To Update

- `frontend/src/App.js`:
  - Remove imports: `QuizPage`, `RecallDashboardPage`, `LessonDashboardPage`, `LessonDetailPage`
  - Remove routes: `/quiz`, `/dashboard`, `/recall`, `/lessons/:lessonId`
  - Change the catch-all redirect from `<Navigate to="/quiz" />` to `<Navigate to="/login" />`
  - Final routes: `/login` → `<Login />`, `/` → redirect to `/login`

- `frontend/src/services/api.js`:
  - Remove all quiz methods: `getNextQuiz`, `submitAnswer`, `getQuizHistory`, `getQuizStats`, `getQuizTopics`, `getQuizEligibility`
  - Remove recall methods: `getRecallMap`, `getTopicMatrix`
  - Remove lesson methods: `getLessons`, `getLessonById`
  - Keep: `login`, `logout`, `getCurrentUser`

#### To Add New
None.

### Documentation

#### Abstract (`docs/abstract/`)

- **Delete**: `docs/abstract/quiz.md`
- **Delete**: `docs/abstract/recall_dashboard.md`
- **Update** `docs/abstract/index.md`:
  - Remove rows for Quiz and Recall Dashboard
  - Result: single row for Authentication only
- **Update** `docs/abstract/authentication.md`:
  - Top nav: change `[Parent](./index.md) | [Next: Quiz >](./quiz.md)` → `[Parent](./index.md)`
  - Bottom nav: same change

#### Technical (`docs/technical/`)

- **Delete**: `docs/technical/quiz.md`
- **Delete**: `docs/technical/recall_dashboard.md`
- **Update** `docs/technical/index.md`:
  - Remove rows for Quiz and Recall Dashboard
  - Result: 2 rows — System Pipelines and Authentication
- **Update** `docs/technical/authentication.md`:
  - Top nav: remove `[Next: Quiz >](./quiz.md)`
  - Bottom nav: same change
- **Update** `docs/technical/system_pipelines.md`:
  - Remove sections: Quiz Selection Pipeline, Quiz Answer Pipeline, Lesson Upload Pipeline, Recall Dashboard Pipeline, Topic Matrix Pipeline
  - Keep: Login Pipeline, Session Restore Pipeline
  - Update bottom nav: remove `[Next: Authentication >](./authentication.md)` if Quiz was referenced; keep only `[Parent](./index.md) | [Next: Authentication >](./authentication.md)`

#### Plan files (`docs/plan/`)

- **Delete** (all superseded by this plan):
  - `docs/plan/260301_quiz.md`
  - `docs/plan/260301_recall_dashboard.md`
  - `docs/plan/260310_lesson_table.md`
  - `docs/plan/260311_lesson_quiz_loop_summary.md`
  - `docs/plan/260312_quiz_question_counter.md`
  - `docs/plan/260314_question_level_recall.md`
  - `docs/plan/260314_loop_completion_navigation.md`

#### Checklist (`docs/checklist.md`)

- **Update**: Remove all existing entries under `## Implementation` and `## DB Cloud Migration` (all are quiz/lesson related)
- Add the new plan entry under `## Implementation`:  `- [ ] docs/plan/260330_remove_quiz_recall_dashboard.md`

### Chrome Claude Extension Execution

After implementation is complete, execute the Chrome Claude Extension E2E tests defined in `docs/chrome_test/remove_quiz_recall_dashboard.md` to verify that authentication remains fully functional after the cleanup.

---

## Dependencies

- Authentication feature must remain intact: `backend/src/api/auth.py`, `backend/src/api/login.py`, `backend/src/models/user.py`, `backend/src/crud/crud_user.py`, `frontend/src/contexts/AuthContext.js`, `frontend/src/components/ProtectedRoute.jsx`, `frontend/src/pages/Login.jsx`.
- The `users` database table must not be dropped.

## Open Questions

None — scope is clear. All quiz, recall dashboard, and lesson files are removed. Authentication is fully preserved.
