# ABAC (Attribute-Based Access Control)

Decide at **request time by evaluating a rule over the properties of *both* the user and the specific resource** (plus context). Because the rule sees the resource, it can *compare* them — the case RBAC can't express. Flexible, but it only compares **flat properties**; it stalls on *chained* relationships (e.g. "a post in a project you belong to"), which are paths through other entities rather than properties of the resource itself.
