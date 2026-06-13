# Semantic caching

A cache that stores past *question→answer* pairs and serves a stored answer when a **new question means the same thing** (matched by embedding similarity, not exact text). It skips the model call entirely — the cheapest possible request. *Example:* Chloe asks "How do I reset my password?" and later Alan asks "I forgot my password, what now?" — the receptionist recognizes these *mean the same thing* and hands back the answer it already has, with no professor consulted at all.
