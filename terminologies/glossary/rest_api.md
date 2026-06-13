# REST API

**RE**presentational **S**tate **T**ransfer: a convention for that client↔server conversation using plain HTTP verbs (`GET` to read, `POST` to create, `PUT`/`PATCH` to update, `DELETE` to remove) on **URLs that name resources**, usually exchanging **JSON**. It's the agreed grammar so both sides understand each other. *Example:* When Chloe's browser wants her profile it sends `GET /api/profiles/chloe`; to post a new note it sends `POST /api/notes` with the note's text as JSON. "GET means fetch, POST means create" — that shared rulebook is the REST API.
