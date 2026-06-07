# Predicate

A small, named, reusable boolean test for one relationship, e.g. `self(column)`, `manager_of(column)`, `whitelist:endpoint`, `any_authenticated`. A rule is predicates combined with `OR`; each predicate compiles to a concrete SQL condition at runtime. This is `/librarian`'s lightweight stand-in for storing tuples in a graph database.
