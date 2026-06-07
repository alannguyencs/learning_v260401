# LLM (e.g., Claude)

The transformer model that, given the user's query plus the available tool list, decides **whether** to call a tool and **which** one (`ToolUse`), then phrases the final answer. It never talks to the API server itself; your app runs whatever it chooses via the MCP Client.
