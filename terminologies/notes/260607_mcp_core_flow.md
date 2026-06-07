## Model Context Protocol (MCP) — the core flow

**In one sentence:** MCP is an open standard that lets your application hand an **LLM** the ability to call an external **API server** (like GitHub) through a uniform interface — your app embeds an **MCP Client** that talks to an **MCP Server**, and that server exposes three primitives: **tools** (live on the server), plus **resources** and **prompts** (predefined, consumed on the client side).

### Key terminologies
Read top to bottom; each builds on the last.

- **Model Context Protocol (MCP)** — The open standard that defines how an AI app talks to external services: the messages they exchange and the capabilities (tools, resources, prompts) a server may expose. The MCP Client and MCP Server are the two endpoints that speak it. *(Introduced by Anthropic, Nov 2024; now an open standard at modelcontextprotocol.io.)*
- **API server (e.g., GitHub)** — The actual external service that holds the data or performs the action (GitHub, a database, a weather API). It knows nothing about MCP — it just answers normal API requests. In the flow it is the rightmost lifeline that returns the real `Response`.
- **LLM (e.g., Claude)** — The transformer model that, given the user's query plus the available tool list, decides **whether** to call a tool and **which** one (`ToolUse`), then phrases the final answer. It never talks to the API server itself; your app runs whatever it chooses via the MCP Client.
- **MCP Server** — An external program that exposes a service's capabilities in MCP format (e.g. a GitHub server wrapping the GitHub API as callable tools). It receives `ListToolsRequest` / `CallToolRequest`, makes the real API call, and returns results. This is where the integration burden lives — written once, reusable by any MCP host.
- **Tools** *(stay in the MCP Server)* — **Model-controlled** executable functions the server exposes (e.g. "list my repositories"). The server ships **both** the schema and the implementation and **runs** them — tools live and execute on the **MCP Server side**. The LLM only decides when to call one; the MCP Client merely relays that call.
- **MCP Client** — The connector library *inside your application* ("Our Server") that holds the connection to one MCP server, sends standardized messages (`ListToolsRequest`, `CallToolRequest`) and reads back replies. It hides all protocol and transport detail so your app focuses on its own logic. Your app talks to the LLM but does **not** speak MCP directly — it delegates that to this client.
- **Resources** *(predefined, stay on the MCP Client side)* — **Application-controlled** read-only data sources identified by a URI (file contents, a DB schema, docs). Like a `GET`: provides context, no side effects. Although the server *offers* them, **control sits on the MCP Client side** — the client/host decides when to pull a predefined resource into the LLM's context.
- **Prompts** *(predefined, stay on the MCP Client side)* — **User-controlled** reusable message templates the server offers (e.g. a "summarize this PR" workflow). Invocation sits on the **MCP Client side** — the user, inside the host/client, explicitly picks one of these predefined templates to run; the server only supplies the template body.
- **MCP Inspector** — A built-in, browser-based testing tool shipped with the Python MCP SDK that lets you exercise a server **without** wiring up a full host/client. Launch it with `mcp dev mcp_server.py`, which serves a local URL (e.g. `http://127.0.0.1:6274`); click **Connect** (status flips *Disconnected → Connected*), then browse the **Tools / Resources / Prompts** tabs to **List** and **Run** each one with live inputs and see the returned data. It keeps server state between calls — so an `edit` then a `read` confirms the change persisted — making it the fast iterate/debug loop for MCP server development.

### The core flow (a GitHub example)
A user asks *"What repos do I have?"*. Six lifelines, left to right: **User → Our Server → MCP Client → MCP Server → LLM → API server**. Note the division of labor — **Our Server** orchestrates the whole loop but never speaks MCP; the **MCP Client** is the only component that talks MCP to the **MCP Server**; the **MCP Server** is the only one that touches the API server. Discovery (`ListTools`) happens once up front; execution (`CallTool`) happens only after the LLM decides to use a tool.

```
 User      Our Server      MCP Client      MCP Server      LLM        API server
  │             │               │               │             │             │
  │─"What repos │               │               │             │             │
  │  do I have?"▶               │               │             │             │
  │             │─"I need tools │               │             │             │
  │             │  for Claude"─ ▶               │             │             │
  │             │               │─ListToolsRequest ─▶         │             │
  │             │◀─"here are     │◀─ListToolsResult ─          │             │
  │             │   the tools"── │               │             │             │
  │             │────────── Query + Tools ───────────────────▶│             │
  │             │◀───────────────── ToolUse ──────────────────│             │
  │             │ ("call this tool with these args")          │             │
  │             │─"please run   │               │             │             │
  │             │  this tool"── ▶               │             │             │
  │             │               │─CallToolRequest ─▶          │             │
  │             │               │               │─ Request to Github ──────▶│
  │             │               │               │◀──────── Response ────────│
  │             │◀─"here's the  │◀─CallToolResult ─           │             │
  │             │   result"──── │               │             │             │
  │             │──────────── toolResult ────────────────────▶│             │
  │◀─"Your      │               │               │             │             │
  │  repos are…"│◀──────── "Your repositories are…" ──────────│             │
  │             │               │               │             │             │
```

---
**Sources:**
- Anthropic Academy — *Introduction to Model Context Protocol* ("How It All Works Together" flow). Merged from the 260607 MCP notes.
