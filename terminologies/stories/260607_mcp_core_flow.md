# Model Context Protocol (MCP)

Let me set the scene with the problem before I give you the word, because the word only makes sense once the problem itches. You've got an **LLM** — Claude, say — and it's brilliant at language, but it's trapped inside its own head. It can't see your GitHub, can't read your database, can't check the weather. The obvious thing is to wire it up to those services, and people did — but everyone wrote their *own* glue, their own bespoke way of describing "here's a tool, here's how you call it." Every app, every service, a new snowflake integration. So somebody asked the sensible question: what if we agreed on *one* standard way for an AI app to talk to external services? That standard is the **Model Context Protocol**, MCP — Anthropic introduced it in November 2024, and it's now an open standard. It defines the messages two endpoints exchange and the capabilities one side may offer the other. Those two endpoints have names we'll build up to: the **MCP Client** and the **MCP Server**.

```
LLM  ──(no standard)──>  GitHub / DB / weather   =  bespoke glue everywhere
MCP  =  one agreed protocol between two endpoints (Client ⇄ Server)
```

Now let's place the characters, starting at the far end, because the far end is the dumbest and that's the point. At the rightmost edge sits the **API server** — the real GitHub, the real database, the real weather API. The **API server** is the thing that actually holds the data or does the work, and here's the crucial detail: the **API server** knows *nothing* about MCP. The **API server** has never heard of MCP. The **API server** just answers ordinary API requests the way it always has. In our story the **API server** is the lifeline on the far right that finally returns the real `Response`.

```
API server (GitHub)  =  the real service, MCP-unaware, just answers normal requests
```

Next to the **API server**, conceptually, is the **LLM** itself — but I want you to notice immediately what the **LLM** does *not* do. Given the user's query plus a list of available tools, the **LLM** decides two things and only two things: *whether* to call a tool at all, and *which* one — that decision is called a `ToolUse`. And later the **LLM** phrases the final human answer. That's the **LLM**'s whole job in this dance. The **LLM** never, ever talks to GitHub itself. The **LLM** just *decides*; your application runs whatever the **LLM** chose. Keep that wall firmly in your mind — the model proposes, something else disposes.

```
LLM:  query + tool list  →  decides WHETHER + WHICH (ToolUse)  →  later phrases answer
       (never touches the API server)
```

So who does the actual touching? The **MCP Server**. The **MCP Server** is an external program that takes a service's capabilities and re-expresses them in MCP format — a GitHub **MCP Server**, for instance, wraps the GitHub API as a set of callable tools. The **MCP Server** is the piece that receives the standardized requests — a `ListToolsRequest` asking "what can you do?", a `CallToolRequest` saying "do this one" — and the **MCP Server** is the *only* component that turns around and makes the real API call, then hands the result back. And here's why MCP is worth anything at all: the **MCP Server** is where the integration burden lives, and it's written *once*. Build the GitHub **MCP Server** one time, and any MCP-speaking app can reuse the **MCP Server**. The snowflake problem dissolves.

```
MCP Server  =  wraps GitHub's API as MCP tools
             →  the ONLY piece that calls the real API
             →  written once, reused by any host
```

Now, what exactly does the **MCP Server** *expose*? Three things, and the difference between them is the heart of today's lecture, so go slow. The first and most important are **tools**. A **tool** is an executable function — "list my repositories," say — and a **tool** is **model-controlled**, meaning the *LLM* decides when to fire the **tool**. But here's the part people get wrong: the **MCP Server** ships *both* the description of the **tool** *and* the **tool**'s implementation, and the **MCP Server** is where the **tool** actually *runs*. **Tools** live and execute on the **MCP Server side**. The **LLM** only picks the moment; the **LLM** doesn't hold the **tool**'s code. Say that back to yourself — the **tool**'s body lives on the **MCP Server**, the decision to use the **tool** lives in the **LLM**.

```
tool  =  model decides WHEN   |   server holds the code AND runs it
         "list my repositories"  →  executes on the MCP Server side
```

But notice the **LLM** can't reach the **MCP Server** directly, and neither does your own application want to learn the whole protocol. That's the gap the **MCP Client** fills. The **MCP Client** is a connector library that sits *inside your application* — in our example we'll call your app "Our Server" — and the **MCP Client** holds the live connection to one MCP server. The **MCP Client** is the thing that sends those standardized `ListToolsRequest` and `CallToolRequest` messages and reads the replies, hiding every grimy detail of protocol and transport so your app can think about its own logic. So your application talks to the **LLM** directly, but your application does *not* speak MCP itself — it delegates all of that to the embedded **MCP Client**. The **MCP Client** is your app's translator.

```
Your app ("Our Server")  ──talks to──>  LLM
        └── embeds ──> MCP Client  ──speaks MCP──>  MCP Server
   (your app never speaks MCP itself)
```

Now back to the three primitives, because tools were only the first, and the other two flip the control around in a way that's easy to muddle. The second is **resources**. A **resource** is read-only data identified by a URI — the contents of a file, a database schema, some documentation. Think of a **resource** like a `GET`: a **resource** supplies context, a **resource** has no side effects. And here's the twist that mirrors tools: even though the **MCP Server** *offers* **resources**, the **control sits on the MCP Client side**. The **MCP Client** or host decides when to pull a predefined **resource** into the **LLM**'s context. Compare that to a **tool** — a **tool** is model-controlled and runs on the **MCP Server**; a **resource** is application-controlled and consumed on the **MCP Client**. Same offering direction, opposite hand on the wheel.

```
tool      →  model-controlled, runs on SERVER
resource  →  app-controlled, pulled in on CLIENT (read-only, like GET)
```

The third primitive is **prompts**, and **prompts** shift control one more notch — to the *user*. A **prompt** is a reusable message template the **MCP Server** offers, like a packaged "summarize this PR" workflow. The **MCP Server** only supplies the **prompt**'s template body; the *invocation* of the **prompt** sits on the **MCP Client** side, because it's the human, inside the host, who explicitly reaches over and picks one of these **prompts** to run. So lay the three side by side and the pattern is clean: **tools** are model-controlled, **resources** are application-controlled, **prompts** are user-controlled — and while **tools** execute on the **MCP Server**, **resources** and **prompts** are predefined and consumed on the **MCP Client** side.

```
tool    →  MODEL picks     (runs on server)
resource→  APP pulls in    (predefined, client side)
prompt  →  USER picks      (predefined, client side)
```

Let me put all of that in motion with the actual flow, the one that ties every term together. A user types *"What repos do I have?"* Picture six lifelines left to right: the **User**, then **Our Server** (your app), then the **MCP Client** it embeds, then the **MCP Server**, then the **LLM**, and finally the **API server**, GitHub. And keep one division of labor in your head as we go: Our Server orchestrates the whole loop but never speaks MCP; the MCP Client is the only thing that talks MCP to the MCP Server; and the MCP Server is the only thing that touches GitHub.

```
User → Our Server → MCP Client → MCP Server → LLM → API server
        (orchestrates)  (speaks MCP)   (calls GitHub)
```

Here's how it actually plays out. The user's question lands on Our Server. Our Server thinks "I need to know what tools Claude has available," so it asks its MCP Client, which sends a `ListToolsRequest` to the MCP Server and gets back the tool list — and notice this *discovery* step happens once, up front. Now Our Server sends the LLM the user's query *plus* that tool list. The LLM looks it over and replies with a `ToolUse` — "call this tool, with these arguments." Our Server says "right, please run this tool," the MCP Client packages it as a `CallToolRequest`, the MCP Server receives it and *now* makes the real request to GitHub, GitHub returns its ordinary `Response`, and the server passes it back as a `CallToolResult`. Our Server feeds that tool result back to the LLM, the LLM finally phrases it in plain English — "Your repositories are…" — and that sentence flows back out to the user. Discovery once with `ListTools`; execution only *after* the model decides, with `CallTool`.

```
ListTools (once)  →  LLM sees tools  →  ToolUse  →  CallTool  →  GitHub  →  result  →  LLM phrases answer
```

Now, before you wire up a whole host and client just to test a server you're building, there's a shortcut I want to leave you with — the **MCP Inspector**. The **MCP Inspector** ships with the Python MCP SDK and the **MCP Inspector** is a browser-based testing tool that lets you exercise a server *without* building any of the surrounding plumbing. You launch the **MCP Inspector** with `mcp dev mcp_server.py`, the **MCP Inspector** serves a local URL like `http://127.0.0.1:6274`, you click **Connect** and watch the status flip from *Disconnected* to *Connected*, and then the **MCP Inspector** lets you browse three tabs that should look familiar by now — **Tools**, **Resources**, **Prompts** — where you can **List** and **Run** each one with live inputs and watch the data come back. And the genuinely useful part: the **MCP Inspector** keeps server state between calls, so you can run an `edit` and then a `read` and confirm the change actually persisted. That's your fast iterate-and-debug loop while developing an MCP server — the same three primitives we just learned, sitting right there as tabs you can poke.

```
mcp dev mcp_server.py  →  http://127.0.0.1:6274  →  Connect
   →  tabs: Tools | Resources | Prompts  →  List / Run, state persists
```

So hold the whole shape in your head as you walk out: MCP is the standard, the API server is the dumb real service at the end, the LLM only decides, the MCP Server does the touching and carries the write-once integration burden, the MCP Client is your app's embedded translator, and the three primitives split cleanly by who's in control — model, application, user — with tools running on the server while resources and prompts are predefined on the client. Get that division of labor right and every arrow in the flow explains itself.
