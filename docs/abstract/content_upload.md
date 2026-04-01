# Content Upload

[Parent](./index.md)

**Status:** Plan

## Related Docs
- Technical: [technical/content_upload.md](../technical/content_upload.md)

## Problem

The app has no content data model. There is no way to store or retrieve books, lessons, chapters, or quizzes. Without content, no learning can occur.

## Solution

A local agent uploads structured content via API using a Bearer token — without direct database access. Content is organized in a four-level hierarchy: books → lessons → chapters → chapter quizzes. All quiz types (free recall, teach-back, cloze, multiple choice) are stored in one unified table.

## User Flow

```
Local agent reads lesson markdown files
        |
        v
POST /api/content/books (Bearer token)
        |
        v
POST /api/content/lessons (Bearer token)
        |
        v
POST /api/content/chapters (Bearer token)
        |
        v
POST /api/content/quizzes (Bearer token, batch)
        |
        v
Content stored in DB: books → lessons → chapters → chapter_quizzes

Frontend fetches available books
        |
        v
GET /api/content/books (session cookie)
        |
        v
GET /api/content/books/{book_id}/structure (session cookie)
```

## Scope
- Included: upload books, lessons, chapters, quizzes via API; list books; book structure view; rich quiz metadata (section labels, takeaways, format-specific fields)
- Not included: manual content entry in UI, content editing or deletion, versioning

## Acceptance Criteria
- [ ] Agent can upload a full book with lessons, chapters, and quizzes via API
- [ ] Upload endpoints reject requests without a valid Bearer token
- [ ] Frontend can list all available books
- [ ] Frontend can retrieve the full hierarchical structure of a book
- [ ] Quiz slides display section name, takeaway, and format-specific metadata after answering

---

[Parent](./index.md)
