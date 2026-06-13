# SQLAlchemy

Python's most popular **ORM** implementation: instead of writing raw SQL strings, you define Python classes that mirror your tables, and SQLAlchemy translates `session.query(User)` into `SELECT ... FROM users` and back into Python objects. It's the translator between "Python objects" and "SQL rows." *Example:* Alan writes `note = Note(text="hi")` and `session.add(note)` in plain Python; SQLAlchemy quietly turns that into the `INSERT INTO notes ...` SQL that Postgres actually understands — so Alan thinks in objects, not in database dialect.
