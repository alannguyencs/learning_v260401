# Relationship tuple

In full ReBAC engines, a relationship is stored as one row of the form `<object>#<relation>@<user>`, e.g. `document:X#editor@bob` ("Bob is an editor of document X"). The whole permission state is just a big set of these tuples.
