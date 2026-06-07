## Key / Value vectors

**In one sentence:** In a transformer's attention, every token is projected into three float vectors — a **query**, a **key**, and a **value** — where the **key** is the token's "matchable" handle and the **value** is the "payload" it hands over when matched; both are vectors of numbers, *not* tokens.

### Key terminologies
These build up to what a key and a value actually are; read top to bottom.

- **Token** — The small unit of text an LLM reads and emits — usually a word piece (e.g. `"paging"` → `pag` + `ing`). It's the model's input/output unit, but attention never works on tokens directly, only on the vectors derived from them; generation is a loop that emits one token per step, and a length-**N** sequence is N tokens, so attention's cost grows with N.
- **Token ID (vocabulary lookup)** — Each token *string* (`"pag"`, `"ing"`) is mapped to a unique integer via a fixed ~128k-entry **vocabulary** dictionary (e.g. `"pag"` → `8472`). This is a plain hash-map lookup — the only step where the characters matter; afterwards the model sees only the integer ID, not the text.
- **Embedding** — The float vector a token is first turned into (e.g. 512 or 4096 numbers). The token ID becomes this vector by **indexing the embedding matrix** `E` (shape `vocab_size × d_model`): the ID is just a row number, so `embedding = E[id]` (e.g. `E[8472]`) simply *retrieves* row 8472 — array indexing, no arithmetic on the text. It's the model's numeric representation of that token's meaning; everything downstream, including keys and values, is computed from it. *Embeddings are learned parameters (the rows of `E`) updated by gradient descent during training — unlike keys/values, which are recomputed activations, not stored weights.*
- **Vector (of floats)** — An ordered list of real numbers, like `[0.2, -1.1, 0.4, …]`. Queries, keys, and values are all vectors of this kind — the "key" is a vector, *not* the token.
- **Projection matrix (W_Q, W_K, W_V)** — Three learned weight matrices. Multiplying a token's embedding by each one produces its query, key, and value vector respectively. "Learned" = adjusted during training by gradient descent.
- **Query (q)** — `q = W_Q · embedding`. The "what am I looking for?" vector for the token currently doing the looking. *Simple example:* like typing **"books about space"** into a library catalog — it's the request this token is making.
- **Key (k)** — `k = W_K · embedding`. The "what do I offer, for matching?" vector. Attention compares queries against keys. *Simple example:* like the **topic label on each book's spine** ("Astronomy", "Cooking") that the catalog checks your search against.
- **Value (v)** — `v = W_V · embedding`. The "what information I contribute if I'm matched" vector — the payload that actually flows into the output. *Simple example:* like the **actual contents of the book** you take home once its label matched your search.
- **Dot product** — `q · k`, a single number measuring how well a query and a key align. Bigger = better match. This is why query and key must have the **same dimension** `d_k`.
- **Softmax** — Turns the raw `q · k` match scores (one per past token) into weights that are positive and sum to 1 — i.e. "how much attention to pay to each token."
- **Key / Value vectors** — The per-token **key** and **value** float vectors that attention reads (both derived from a token's embedding — not the token itself). The **key** is matched against a query via dot product to decide *how much* attention each token gets; the **value** is the payload those weights sum over to decide *what* information is passed on.

### How these terms are related
Each step forces the next:

1. **Token → token ID.** The token *string* is mapped to an integer via the **vocabulary** dictionary (`"pag"` → `8472`) — a hash-map lookup, the last point where the text matters.
2. **Token ID → embedding.** The integer ID indexes a row of the embedding matrix `E` (`E[8472]`), retrieving that token's float **embedding** — attention needs numbers, not text. The "conversion to a vector" is a lookup, not a computation.
3. **Embedding → three projections.** The embedding is multiplied by the three learned matrices **W_Q / W_K / W_V**, producing the token's **query**, **key**, and **value** vectors. All three are float vectors derived from the *same* embedding.
4. **Query · Key → match score.** To decide where to look, the current token's **query** is **dot-producted** with every past token's **key**, giving one raw score per token. (This is why `q` and `k` share dimension `d_k`.)
5. **Scores → softmax weights.** Divide the scores by `√d_k` (keeps them numerically stable) and apply **softmax** → a set of weights that sum to 1.
6. **Weights × Values → output.** The output for the current position is the **weighted sum of the value vectors**: `z = Σ αⱼ · vⱼ`. The key decided *how much*; the value decided *what*.
7. **Why two vectors (k and v).** Because matching ("is this a location word?") and retrieving ("here's the location info") are different jobs, the key and value are separate projections — and `v` may even have a different dimension `d_v` than `d_k`.

**The chain in one line:**
`token → token ID (vocab lookup) → embedding (E[id]) → (W_K, W_V) → key + value → query·key (dot product) → softmax → Σ weight·value → attention output`

### Concrete example
A tiny PyTorch-style sketch of single-head self-attention — watch the key and value do their separate jobs:

```python
import torch

x  = embeddings              # (T, d)  one float vector per token
Wq, Wk, Wv = Wq, Wk, Wv      # learned: (d, d_k), (d, d_k), (d, d_v)

Q = x @ Wq                   # (T, d_k)  queries
K = x @ Wk                   # (T, d_k)  KEYS  — used only to be matched
V = x @ Wv                   # (T, d_v)  VALUES — used only to be summed

scores  = Q @ K.transpose(0, 1) / d_k**0.5   # (T, T)  query·key match scores
weights = scores.softmax(dim=-1)             # (T, T)  rows sum to 1
out     = weights @ V                        # (T, d_v)  blend of VALUE vectors
```

For the token `"on"` in `"The cat sat on the ___"`: `K["on"]` is matched against the
current query; if it scores high, `V["on"]` (carrying "a surface/location comes next")
dominates the blended `out`, nudging the model toward `"mat"`. `K["on"]` and `V["on"]`
are both rows of floats — the word `"on"` itself never enters the arithmetic.

### Where you'll meet it
- **Every transformer** — GPT, Llama, BERT, T5, ViT. The Q/K/V projection is the heart of the attention block.
- **The KV cache** — at generation time, models store each past token's **key and value vectors** (not the tokens) so they aren't recomputed every step; this is what `PagedAttention` / vLLM optimize. See [[260604_vllm]].
- **Multi-head attention** — each "head" has its own `W_Q/W_K/W_V`, so a token has several key/value pairs, one per head.
- Courses: any modern deep-learning / NLP course covering "Attention Is All You Need."

### Common confusions
- **"The key is the token."** No — the key is a *float vector* computed from the token's embedding. The token only appears at the very start (→ embedding) and very end (→ next-token probabilities).
- **Key vs Value.** Same shape-ish, opposite roles: the **key** is what you *match against* (used in `q·k`); the **value** is what you *get back* (summed by the weights). One is the index, the other is the payload.
- **Query vs Key.** A query is "what I'm looking for"; a key is "what I offer to be found by." In self-attention every token produces all three; in cross-attention queries come from one sequence, keys/values from another.
- **d_k vs d_v.** Query and key must share dimension `d_k` (they're dot-producted); the value dimension `d_v` is independent and sets the output size.

---
**Sources:**
- [Understanding and Coding the Self-Attention Mechanism (Sebastian Raschka)](https://sebastianraschka.com/blog/2023/self-attention-from-scratch.html)
- [Query, Key, and Value (QKV) in the Transformer Architecture — Ebrahim Pichka](https://epichka.com/blog/2023/qkv-transformer/)
- [Query, Key, and Value Vectors in Self-Attention — APXML](https://apxml.com/courses/introduction-to-transformer-models/chapter-2-self-attention-multi-head-attention/query-key-value-vectors)
- [Self-Attention in NLP — GeeksforGeeks](https://www.geeksforgeeks.org/nlp/self-attention-in-nlp/)
