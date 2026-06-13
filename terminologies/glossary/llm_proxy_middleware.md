# LLM proxy / middleware

A software layer placed **between your app and the provider** that intercepts every request and transparently applies optimizations before forwarding it. (Middleware = code that sits in the request path and pre-processes traffic, like Express/FastAPI middleware.) *Example:* Instead of Alan's app phoning the model directly, a clever receptionist sits in the middle, looks at each question first, and decides how to handle it cheaply before passing it on.
