# MCP Client

The connector library *inside your application* ("Our Server") that holds the connection to one MCP server, sends standardized messages (`ListToolsRequest`, `CallToolRequest`) and reads back replies. It hides all protocol and transport detail so your app focuses on its own logic. Your app talks to the LLM but does **not** speak MCP directly — it delegates that to this client.
