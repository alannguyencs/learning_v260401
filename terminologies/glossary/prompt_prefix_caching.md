# Prompt (prefix) caching

A *provider-side* cache that reuses the GPU's internal work (the **KV cache**, see [[kv-cache-key-value-cache]]) for a **repeated leading chunk** of the prompt — a system prompt or shared document — so the unchanged prefix isn't recomputed each call. Complements semantic caching rather than replacing it. *Example:* Every one of Alan's questions starts with the same long "You are a helpful tutor…" preamble; the provider remembers the work it already did on that preamble instead of re-reading it from scratch every single time.
