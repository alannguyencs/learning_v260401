# KV cache (Key–Value cache)

Instead of recomputing every past token's key/value vectors on each step, the model **saves them** and reuses them. That saved store is the KV cache; it grows by one slot per generated token and lives in GPU memory.
