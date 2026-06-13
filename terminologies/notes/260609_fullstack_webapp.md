## Full-Stack Web Application (FastAPI + SQLAlchemy + PostgreSQL + React + Vite + Tailwind)

**In one sentence:** A **full-stack web application** is the whole running system — a database, a server that talks to it, and a browser UI that talks to the server — and this particular stack wires a Python **FastAPI**/**SQLAlchemy**/**PostgreSQL** backend to a **React 18**/**Vite**/**Tailwind** frontend, kept in one **monorepo**, talking over **REST**, sharing one login **cookie** for **SSO**, and shipped automatically by **GitHub Actions**.

### Key terminologies
The chart below is the map of the whole stack: data lives at the bottom-left (Postgres), flows up through the backend, crosses the REST contract to the frontend, and the bottom band (monorepo, SSO, CI/CD) are the cross-cutting concerns that wrap the whole thing. Read the bullets in the same order — foundational ideas first, the full-stack app last.

```
Client–server model            (browser asks, server answers)
        │
        ▼
HTTP / HTTPS  ─────────  the transport (HTTPS = HTTP + encryption)
        │
        ▼
REST API  ──────┬──────  the request/response contract (HTTP verbs + JSON)
        │       └─ WebSocket  (alternative: persistent 2-way real-time channel)
   ┌────┴──────────────── BACKEND ──────────────────┐
   │                                                 │
   ▼                                                 │
FastAPI         (Python framework: receives requests)│
   │              └── Pydantic validates request/response JSON
   ▼                                                 │
Middleware      (wraps every request: auth, logging) │
   │              └── sets CORS headers (cross-origin permission)
   ▼                                                 │
ORM             (the idea: map objects  ⇄  tables)   │
   │                                                 │
   ▼                                                 │
SQLAlchemy      (Python's ORM implementation)        │
   │                                                 │
   ▼                                                 │
PostgreSQL      (the relational database, the truth) │
                                                     │
   ┌──────────────────── FRONTEND ──────────────────┘
   │
   ▼
SPA             (one HTML page, JS swaps the content)
   │
   ▼
React 18        (builds the UI out of components)
   │
   ▼
Vite            (dev server + bundler that runs React)
   │              └── dev proxy forwards /api → backend (skips CORS in dev)
   ▼
Tailwind CSS    (utility classes that style the UI)
   │
   ▼  ── cross-cutting concerns wrap everything above ──
Monorepo        (backend + frontend live in ONE repo)
   │
   ▼
Shared-cookie SSO   (one login cookie, many apps trust it)
   │              ├── carries a JWT (signed identity token)
   │              └── OAuth / OIDC (how the login itself happens)
   ▼
Docker          (package each part into a portable container)
   │
   ▼
GitHub Actions CI/CD   (auto-test + auto-deploy on every push)
   │
   ▼
FULL-STACK WEB APPLICATION   (all of the above, working as one product)
```

- **Client–server model** — The bedrock pattern of the web: a **client** (the browser) sends requests, a **server** (your backend) processes them and sends responses. Neither trusts the other's memory — every request stands alone. *Example:* Chloe opens the app in her browser (the client) and it shouts a question across the internet to Alan's server: "give me Chloe's profile." The server does the work and shouts the answer back. They never share a brain — every time Chloe wants something, her browser has to ask again.
- **HTTP vs HTTPS** — **HTTP** (HyperText Transfer Protocol) is the rulebook for the request/response messages the browser and server send — the **transport** that carries everything. **HTTPS** is the *same* protocol wrapped in **TLS encryption**, so the messages are scrambled in transit and the server's identity is proven by a **certificate**; the `S` is for "Secure." Plain HTTP can be read or altered by anyone on the network; HTTPS can't. Today HTTPS is mandatory in production (cookies, JWTs, and passwords must never travel over plain HTTP). *Example:* When Chloe's browser sends her login over plain `http://`, anyone on the café Wi-Fi could read her password in clear text. Over `https://`, that same message is encrypted into gibberish for everyone except Alan's server — and the padlock in her address bar means the certificate proved she's really talking to his server, not an impostor.
- **REST API** — **RE**presentational **S**tate **T**ransfer: a convention for that client↔server conversation using plain HTTP verbs (`GET` to read, `POST` to create, `PUT`/`PATCH` to update, `DELETE` to remove) on **URLs that name resources**, usually exchanging **JSON**. It's the agreed grammar so both sides understand each other. *Example:* When Chloe's browser wants her profile it sends `GET /api/profiles/chloe`; to post a new note it sends `POST /api/notes` with the note's text as JSON. "GET means fetch, POST means create" — that shared rulebook is the REST API.
- **WebSocket** — A protocol for a **persistent, two-way connection** between browser and server: it starts as a normal HTTP request that "upgrades" into a long-lived open pipe, after which *either* side can push messages at any time without a fresh request. It's the alternative to REST when you need **real-time** updates instead of request-and-wait. (Like HTTP, it has a secure `wss://` form over TLS.) *Example:* REST is Chloe *asking* "any new notes?" over and over; a WebSocket is Alan's server keeping a line open to her browser and *shouting* "new note!" the instant one arrives — so a live chat or notification badge updates immediately, with no polling. REST handles her normal save/load; the WebSocket handles the live stuff.
- **FastAPI** — A modern **Python web framework** for building APIs fast. You write functions decorated with the route they handle (`@app.get("/notes")`); it validates incoming data with **Pydantic**, runs **async** so it handles many requests at once, and auto-generates interactive API docs. This is the backend's front door. It's one of several Python web frameworks — siblings include **Django** (batteries-included, with its own ORM and admin UI, great for full sites), **Flask** (a minimal "microframework" you assemble yourself), **Django REST Framework** (Django's add-on for building REST APIs), and **Litestar** / **Starlette** (the async toolkit FastAPI itself is built on). *Example:* Alan writes a Python function and tags it `@app.get("/api/notes/{id}")`; FastAPI makes sure the `id` really is a number, calls the function, and ships the result back as JSON — and throws in a free `/docs` page where Chloe's request can be tried out by hand. He picked FastAPI over Django because he only needs a JSON API, not a whole templated website, and over Flask because he wanted the async speed and automatic validation for free.
- **Pydantic** — The Python **data-validation library FastAPI is built on**: you declare the *shape* of request and response bodies as typed classes (**schemas / DTOs**, e.g. `text: str`), and Pydantic automatically checks incoming JSON against that shape — rejecting malformed data with a clear error — and serializes outgoing objects back to JSON. It's what turns loose JSON into trustworthy typed objects (and powers FastAPI's auto-docs). *Example:* Alan declares a `NoteIn` schema with one field `text: str`; when Chloe POSTs a note, Pydantic confirms `text` really is a string and auto-rejects the request with a `422` if she somehow sends a number — so Alan's handler never has to hand-check the input, it just receives a clean `NoteIn` object.
- **Middleware** — Code that sits **between the request arriving and your route handler running**, wrapping *every* request so it can act on all of them in one place — checking auth, adding CORS headers, logging, timing. Each piece can run logic on the way **in** and again on the way **out**. *Example:* Before any of Alan's route functions run, a CORS middleware stamps the right headers so Chloe's browser is allowed to talk to the server, and an auth middleware peeks at her cookie to figure out who she is — written once, applied to every endpoint automatically, instead of repeating those checks in each handler.
- **CORS (Cross-Origin Resource Sharing)** — A **browser security rule**: by default a page loaded from one **origin** (scheme + domain + port, e.g. `http://localhost:3999`) is *blocked* from calling an API on a *different* origin (e.g. `http://localhost:8999`). The server must opt in by sending `Access-Control-Allow-Origin` headers naming who's allowed — usually configured as **middleware**. It protects users from malicious sites silently calling APIs as them. *Example:* Chloe's React app runs on port 3999 but Alan's API lives on port 8999 — different origins, so her browser refuses the call until Alan's CORS middleware adds a header saying "3999 is allowed." That's also why a random evil site can't quietly hit Alan's API using Chloe's logged-in cookie: the browser won't let it cross origins without permission.
- **ORM (Object–Relational Mapping)** — The general *technique* (and the kind of library implementing it) for bridging the gap between **objects in code** and **rows in a relational database**: you work with classes and objects, and the ORM auto-generates the SQL to load/save them. SQLAlchemy is one specific ORM; the idea is language-agnostic. See [[260609_orm]]. *Example:* The two worlds don't match — in Alan's code `chloe.bestFriend` is a pointer to another object, but in the database it's just a number in a column. An ORM is the translator that reconciles that mismatch automatically, so Alan never has to hand-stuff columns into objects.
- **SQLAlchemy** — Python's most popular **ORM** implementation: instead of writing raw SQL strings, you define Python classes that mirror your tables, and SQLAlchemy translates `session.query(User)` into `SELECT ... FROM users` and back into Python objects. It's the translator between "Python objects" and "SQL rows." *Example:* Alan writes `note = Note(text="hi")` and `session.add(note)` in plain Python; SQLAlchemy quietly turns that into the `INSERT INTO notes ...` SQL that Postgres actually understands — so Alan thinks in objects, not in database dialect.
- **PostgreSQL** — A free, industrial-strength **relational database**: data lives in tables with rows and columns, related tables joined by keys, and every change protected by transactions (all-or-nothing). It's where the *real, permanent* data sits. *Example:* Every note Chloe has ever written is a row in a `notes` table inside Postgres, and her account is a row in a `users` table linked to those notes by her user id. Close the browser, reboot the server — the rows are still sitting there, safe.
- **SPA (Single-Page Application)** — A frontend model where the browser loads **one HTML page once**, and JavaScript then **rewrites the content in place** as the user navigates — fetching data over the API instead of asking the server for a whole new page each click. The result feels like a desktop app: no full-page reloads. It's *why* you need client-side routing and a dev proxy in the first place. *Example:* When Chloe clicks from her note feed to her profile, the page doesn't blank-and-reload — React just swaps the feed component for the profile component and fetches her profile JSON in the background. The URL still changes, but it's one continuous page the whole time. (The opposite is the old model where every click fetched a fresh HTML page from the server.)
- **React 18** — A JavaScript **frontend framework for building user interfaces** out of reusable **components** (self-contained pieces of UI). (Strictly, React bills itself as a *library* rather than a full framework — see Common confusions below — but in everyday usage it's spoken of as *the* frontend framework of this stack.) It keeps a virtual copy of the page and re-renders only what changed when data updates, so the screen always reflects the current **state**. This is what Chloe actually sees and clicks. It's one of several component-based frontend tools — siblings include **Vue** (gentle learning curve, template-based), **Angular** (a heavyweight, batteries-included *framework* with built-in routing/forms), **Svelte** (compiles components away at build time for tiny, fast output), **SolidJS** (React-like syntax with finer-grained updates), and meta-frameworks built *on top* of React like **Next.js** and **Remix** that add routing and server rendering. *Example:* The little `<NoteCard>` box that shows one note is a React component; render it once per note and you get Chloe's whole feed. When she deletes a note, React notices the data changed and silently redraws just that one card — not the entire page. Alan picked React over Angular because he wanted a lightweight library he could pair with his own tools (Vite, his own router), not a full opinionated framework, and over Vue/Svelte mostly for its huge ecosystem and hiring pool.
- **Vite** — A fast **frontend build tool and dev server**. During development it serves your React code to the browser instantly (no slow rebuild on every save); for production it **bundles** everything into small optimized files. It's the engine that runs and packages the frontend. *Example:* While Alan edits a button's color, Vite updates it in Chloe's-eye-view in the browser the instant he hits save — no waiting. When it's time to ship, Vite squashes all the React files into a few tiny ones the browser can download quickly.
- **Dev proxy** — A **development-only** shortcut: the frontend dev server forwards API calls (paths like `/api/*`) to the backend running on a different port, so to the browser everything appears to come from **one origin** and **CORS** never trips. Configured in Vite's `server.proxy` (or Create-React-App's `setupProxy.js`). It exists only locally — in production a real **reverse proxy** does the same routing. *Example:* In dev Chloe's React app on port 3999 calls `/api/notes`; the dev proxy quietly relays it to the backend on 8999 and hands the answer back, so the browser thinks it never left port 3999 — no cross-origin block, no CORS config needed while Alan is coding. (It's the flip side of the **CORS** entry: CORS is the server granting cross-origin permission; the dev proxy avoids being cross-origin in the first place.)
- **Tailwind CSS** — A **utility-first CSS framework**: instead of writing separate stylesheets, you style elements by stacking tiny single-purpose classes right in the markup (`class="flex gap-2 rounded bg-blue-500 p-4"`). Styling happens inline, fast, without inventing class names. *Example:* To make Chloe's note cards rounded with padding and a blue background, Alan just sprinkles `rounded p-4 bg-blue-500` onto the element — no flipping to a separate `.css` file to dream up a name like `.note-card-wrapper`.
- **Monorepo** — Short for "mono-repository": keeping the **backend and frontend (and shared config) together in one Git repository** instead of two. One clone, one version history, one place to change an API and its UI together. Note it's a **different axis from "full-stack"**: *full-stack* describes *how many layers* you build (front + back + DB — a matter of **scope**), while *monorepo* describes *how many repos* you store them in (a matter of **code layout**). They're independent — a full-stack app could split into two repos (multi-repo), and a UI-less set of microservices could still live in one monorepo. *Example:* Alan's `backend/` and `frontend/` folders sit side-by-side in a single repo. When he renames a field in the API, he fixes the server code and the React code that reads it in the *same commit* — they can never drift out of sync because they ship together. His app is *both* full-stack (he owns every layer) *and* a monorepo (those layers live in one repo) — but he could have kept it full-stack while splitting `backend/` and `frontend/` into two separate repos.
- **Shared-cookie SSO** — **S**ingle **S**ign-**O**n via a shared **cookie**: the user logs in once on a main site, the server hands the browser an `HttpOnly` session **cookie** scoped to a shared domain, and every sibling app on that domain trusts the same cookie — so the user is automatically logged in everywhere without logging in again. *Example:* Chloe signs in once on the company's main website; it drops a cookie in her browser. When she clicks over to the payslip app on the same domain, her browser quietly sends that same cookie along, the app sees it and says "ah, this is Chloe" — no second login screen.
- **JWT (JSON Web Token)** — A **signed, self-contained identity token**: a compact string (`header.payload.signature`) that encodes *who the user is* plus an expiry, signed with a secret so the server can verify it wasn't tampered with — **without** looking anything up in a database. It's often the contents that ride *inside* the SSO cookie. *Example:* When Chloe logs in, the server hands her a JWT that effectively says "this is Chloe, valid until 5pm," signed so nobody can forge it. On each later request her browser sends it back (tucked inside the cookie); the server just re-checks the signature and trusts it — no database hit to re-confirm she's still Chloe.
- **OAuth / OIDC** — **OAuth 2.0** is the standard protocol for **delegated authorization**: a user lets one app act on their behalf at another service *without handing over their password*, by redirecting to that service and coming back with a **token**. **OpenID Connect (OIDC)** is a thin layer on top that adds *authentication* — proving *who* the user is (the "Log in with Google" flow). It's the machinery that issues the identity behind a **JWT** / SSO session. *Example:* Instead of Alan's app storing Chloe's password, it bounces her to Google; she approves, Google redirects back with a signed token saying "this is Chloe," and Alan's app trusts it. Chloe never typed a password into Alan's app at all — that delegation dance is OAuth, and the "who is she" part is OIDC.
- **Docker** — A **containerization** tool that packages an app *with* its exact dependencies, runtime, and config into a portable **image** that runs identically anywhere — your laptop, a teammate's, or production — eliminating "works on my machine." A running image is a **container**: lightweight, isolated, but sharing the host OS kernel (unlike a full virtual machine). *Example:* Alan builds one Docker image for his FastAPI backend and another for the frontend; whoever runs them — Chloe's laptop or the production server — gets the exact same Python version, libraries, and settings, so the app behaves the same everywhere. The CI/CD pipeline builds these images and ships the containers.
- **GitHub Actions CI/CD** — GitHub's built-in automation. **CI** (Continuous Integration) auto-runs your linters and tests on every push so broken code can't merge; **CD** (Continuous Deployment) auto-builds and ships passing code to a server. You describe the steps in a YAML file and GitHub runs them for you. *Example:* The moment Alan pushes a commit, GitHub spins up a fresh machine, runs all the tests, and only if they pass does it copy the new code onto the live server — so Chloe gets the update without Alan ever logging into a server by hand.
- **Full-Stack Web Application** — The complete product: the **front** of the stack (what the user sees — React/Vite/Tailwind) plus the **back** of the stack (server + database — FastAPI/SQLAlchemy/PostgreSQL) plus the plumbing that connects and ships them (REST, monorepo, SSO, CI/CD). "Full-stack" means you own *every layer* from the pixel to the database row. *Example:* When Chloe clicks "save note," that one click travels the whole stack — React fires a REST call, FastAPI catches it, SQLAlchemy writes a row, Postgres stores it — and every tech in this list did its job for a single button press. That entire end-to-end thing is the full-stack web app.

### How these terms are related
Read this as a cause-and-effect chain — each step forces the next:

1. **Client–server model → you need a way to carry messages.** The browser and server are separate machines, so they need a transport protocol to ship requests and responses: **HTTP**, secured in production as **HTTPS** (HTTP + TLS encryption) so nobody on the network can read or tamper with the traffic.
2. **HTTP/HTTPS → you need a contract on top of it.** The protocol carries bytes, but both sides must agree what the messages *mean*. That agreement is the **REST API** (HTTP verbs + JSON on resource URLs) — or, when you need the server to push updates in real time rather than answer one request at a time, a **WebSocket** opens a persistent two-way channel instead.
3. **REST API → something must answer the requests.** A program has to receive `GET /api/notes`, run logic, and reply. That's **FastAPI**, the Python web framework serving as the backend's front door. It uses **Pydantic** to validate each incoming JSON body against a declared schema, so the handler only ever sees clean, typed data.
4. **Every request needs the same gate → middleware.** Auth checks and CORS headers shouldn't be copy-pasted into each handler, so **middleware** wraps every incoming request in one place before it reaches the route. One job it handles there: **CORS** — because the React app and the API sit on different origins, the middleware must send the headers that tell the browser the cross-origin call is allowed. (During local development a **dev proxy** sidesteps this by making the frontend and API look like one origin.)
5. **FastAPI → it needs data, but raw SQL is painful.** The handler must read/write persistent data; hand-writing SQL strings and stuffing the results into objects is repetitive, so it uses an **ORM** to work in objects instead.
6. **ORM → pick a concrete one for Python.** The ORM is the general technique; **SQLAlchemy** is the specific library that implements it in this stack.
7. **SQLAlchemy → it needs a real database underneath.** The ORM only translates; the bytes have to live somewhere durable and transactional. That's **PostgreSQL**.
8. **Backend exists → now a human needs to see it.** An API returning JSON is useless to Chloe directly; the frontend is built as a **SPA** (one page, JS swaps the content), and **React 18** turns that JSON into the clickable UI components inside it.
9. **React → it needs to be run and packaged.** React code can't ship raw to the browser; **Vite** serves it instantly in dev and bundles it for production.
10. **UI exists → it needs to look right.** Styling the components by hand is tedious; **Tailwind CSS** does it with utility classes inline.
11. **Two codebases → keep them in sync.** Backend and frontend change together, so they live in one **monorepo** — one commit changes both.
12. **Many requests → prove who's calling.** The stateless server can't tell who Chloe is on each request, so a **shared-cookie SSO** session rides along on every call to identify her across all the company's apps.
13. **SSO cookie → what's inside it, and how is it issued?** The cookie carries verifiable identity without a database lookup each time, so it holds a **JWT** — a signed token the middleware checks on every request — and that token is minted by an **OAuth / OIDC** login flow (e.g. "log in with Google") so the app never handles the password itself.
14. **It all works locally → package it so it runs the same anywhere.** "Works on my machine" isn't enough, so each part is built into a **Docker** image — a portable container bundling the app with its exact dependencies.
15. **Containers built → ship them safely and repeatedly.** Manual testing and deploying is error-prone, so **GitHub Actions CI/CD** auto-tests every push, builds the Docker images, and deploys the passing result.
16. **All layers + plumbing together → the product.** Front (SPA/React/Vite/Tailwind) + back (FastAPI/Pydantic/middleware/SQLAlchemy/Postgres) + connective tissue (HTTPS/REST/monorepo/SSO+JWT+OAuth/Docker/CI-CD) *is* the **full-stack web application**.

**The chain in one line:**
`client–server → HTTP/HTTPS → REST API (or WebSocket) → FastAPI (+Pydantic) → middleware → ORM → SQLAlchemy → PostgreSQL → SPA → React → Vite → Tailwind → monorepo → shared-cookie SSO → JWT (← OAuth/OIDC) → Docker → GitHub Actions CI/CD → full-stack web app`
(two machines → transport → contract / real-time channel → backend+validation → request gate → object↔table technique → its Python impl → DB → app model → UI → tooling → styling → one repo → auth → signed token ← login flow → containerize → automation → the product)

### Concrete example
Trace one click — Chloe saves a note — through every layer of the stack.

**Frontend (React + Vite + Tailwind)** — a component fires a REST call:
```jsx
function SaveNote({ text }) {
  const save = async () => {
    await fetch("/api/notes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",          // <-- sends the shared SSO cookie
      body: JSON.stringify({ text }),
    });
  };
  // Tailwind utility classes do the styling, no separate CSS file:
  return <button onClick={save} className="rounded bg-blue-500 px-4 py-2 text-white">Save</button>;
}
```
Vite serves this during dev and bundles it for production; the `credentials: "include"` is what makes the browser attach the **SSO cookie**.

**Backend (FastAPI + SQLAlchemy + PostgreSQL)** — the matching route:
```python
@app.post("/api/notes")                 # FastAPI: the REST endpoint
def create_note(payload: NoteIn, user=Depends(current_user), db=Depends(get_db)):
    note = Note(text=payload.text, user_id=user.id)   # SQLAlchemy ORM object
    db.add(note)                                       # -> INSERT INTO notes ...
    db.commit()                                        # committed into PostgreSQL
    return {"id": note.id, "text": note.text}          # JSON back across REST
```
`current_user` reads the **shared cookie** to know it's Chloe; SQLAlchemy turns the `Note` object into an `INSERT`; Postgres stores the row durably; FastAPI returns JSON.

**Repo layout (monorepo) + automation (GitHub Actions):**
```
my-app/                      # ONE monorepo
├── backend/                 # FastAPI + SQLAlchemy
├── frontend/                # React + Vite + Tailwind
└── .github/workflows/ci.yml # GitHub Actions: test on push, deploy if green
```
Every term in the list just did its job for a single button press — that end-to-end flow *is* the full-stack web application.

### Where you'll meet it
- **The official [Full-Stack FastAPI Template](https://github.com/fastapi/full-stack-fastapi-template)** — Tiangolo's own boilerplate: FastAPI + SQLModel/SQLAlchemy + PostgreSQL + React + Vite + GitHub Actions. The canonical version of this exact stack.
- **Startups and internal tools** — this Python-backend + React-frontend combo is one of the most common 2025–2026 stacks for SaaS dashboards and company ERP/admin apps (e.g. payslip/expense systems).
- **University capstone & bootcamp projects** — FastAPI's auto-docs and React's component model make this a go-to teaching stack.
- **Your own `learning_v2604` and `fullstack_amazing_grace_v2`** — both are layered FastAPI + SQLAlchemy + Postgres + React apps; the latter uses Vite + shared-cookie SSO exactly as described here.

### Common confusions
- **Full-stack vs. front-end vs. back-end** — "back-end" = server + DB (FastAPI/Postgres); "front-end" = browser UI (React); "full-stack" = you own *both* plus the glue. It's a scope, not a single technology.
- **Library vs. framework (React vs. FastAPI)** — React calls itself a *library* (you assemble the rest yourself); FastAPI is a *framework* (it dictates more of the structure). In practice both are the backbone of their side.
- **SQLAlchemy vs. PostgreSQL** — SQLAlchemy is Python code that *generates* SQL; PostgreSQL is the actual database *engine* that runs it. The ORM can talk to other databases too; swapping Postgres for SQLite barely changes the Python.
- **Vite vs. React** — Vite doesn't build UI; it's the dev-server/bundler that *runs and packages* React (it replaced the older Create-React-App tooling). Different jobs.
- **Shared-cookie SSO vs. JWT-in-header** — both prove identity, but a cookie is set/sent automatically by the browser and shared across same-domain apps (great for SSO), while a JWT bearer token is attached manually per request. Some stacks use one, some the other, some both.
- **Monorepo vs. monolith** — a *monorepo* is one repository holding possibly-separate apps; a *monolith* is one deployed program. You can have a monorepo of microservices, or a monolith split across many repos. Different axes.

---
**Sources:**
- [Full Stack FastAPI Template — GitHub (fastapi/full-stack-fastapi-template)](https://github.com/fastapi/full-stack-fastapi-template)
- [Full Stack FastAPI Template — FastAPI docs](https://fastapi.tiangolo.com/project-generation/)
- [The power of the monorepo: keep your fullstack app in sync — LaunchDarkly](https://launchdarkly.com/docs/tutorials/keeping-your-frontend-and-backend-in-sync-with-a-monorepo)
- [Protecting Single Page Apps with the Token Handler Pattern — Curity](https://curity.io/resources/learn/the-token-handler-pattern/)
- [Cross-Origin Cookie Authentication — CodeSignal](https://codesignal.com/learn/courses/enabling-customizing-cors-in-your-python-rest-api/lessons/cross-origin-cookie-authentication)
- [GitHub Actions — official features page](https://github.com/features/actions)
- [GitHub Actions CI/CD: The Complete Guide for 2026 — DevToolbox](https://devtoolbox.dedyn.io/blog/github-actions-cicd-complete-guide)
