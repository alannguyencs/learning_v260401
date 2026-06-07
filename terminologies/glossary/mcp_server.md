# MCP Server

An external program that exposes a service's capabilities in MCP format (e.g. a GitHub server wrapping the GitHub API as callable tools). It receives `ListToolsRequest` / `CallToolRequest`, makes the real API call, and returns results. This is where the integration burden lives — written once, reusable by any MCP host.
