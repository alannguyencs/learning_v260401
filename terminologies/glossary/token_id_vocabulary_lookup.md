# Token ID (vocabulary lookup)

Each token *string* (`"pag"`, `"ing"`) is mapped to a unique integer via a fixed ~128k-entry **vocabulary** dictionary (e.g. `"pag"` → `8472`). This is a plain hash-map lookup — the only step where the characters matter; afterwards the model sees only the integer ID, not the text.
