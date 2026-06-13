# RBAC (Role-Based Access Control)

Looks at **the user only**. Decide from a **label granted to the user**: bundle permissions into **roles** (`admin`, `editor`, `viewer`), assign roles to users, allow if the user holds a role that grants the action. *Example:* Alan has the `editor` role, so he can edit **any** post on the site — the rule looks only at his role, never at which post it is.
