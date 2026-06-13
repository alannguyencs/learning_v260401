# ABAC (Attribute-Based Access Control)

Looks at **the thing being touched too**, not just the user. Decide by **comparing details of the user with details of the specific resource** — the case RBAC can't handle. ABAC's limit: ABAC can only compare **direct details** of the two, not relationships that run **through other things** (e.g. "a post in a project you belong to"). *Example:* the rule "you may edit a post only if you wrote it" lets Alan edit **his own** posts but not Chloe's.
