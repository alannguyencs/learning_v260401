# API server (e.g., GitHub)

The actual external service that holds the data or performs the action (GitHub, a database, a weather API). It knows nothing about MCP — it just answers normal API requests. In the flow it is the rightmost lifeline that returns the real `Response`.
