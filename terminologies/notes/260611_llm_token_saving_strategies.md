## LLM Token Saving Strategies

**In one sentence:** LLM token saving strategies are the techniques — context compression, model routing, and caching — that an **LLM proxy** applies between your app and the model provider so you spend the fewest (and cheapest) tokens per answer, with **output tokens** mattering most because the GPU generates them one slow, expensive step at a time.

### Key terminologies
This chart is the map of the whole section: foundational ideas at the top flow down and combine into the three proxy levers, which together *are* the token-saving strategy.

```
Token (text unit billed per-piece)
   │
   ├──────────────┐
   ▼              ▼
Input token    Output token        (branch: prefill, parallel & cheap  ──vs──  decode, sequential & 3–5× costlier)
   │              │
   └──────┬───────┘
          ▼
Premium LLM call  ── Cheap LLM call   (branch: smart/expensive  ──vs──  small/cheap — same job, very different price)
          │
          ▼
LLM proxy / middleware   (a layer that sits between your app and the provider)
          │
   ┌──────────────┼──────────────────────┐
   ▼              ▼                       ▼
Context management   Model routing      Semantic caching
(compress input      (pick cheap        (reuse old answers
 before sending)      vs premium)        for similar questions)
   │              │                       │
   └──────────────┴───────────┬───────────┘
                       ▼
        LLM Token Saving Strategies   (the payoff — all three levers, pulled together)
```

These build on each other; read top to bottom and the last term falls out naturally. Anchor: a **token** is to an LLM what a character is to `strlen()` — the atomic unit it counts, except here every unit costs money.

- **Token** — The small chunk of text an LLM reads and writes — usually a word-piece (e.g. `"caching"` → `cach` + `ing`). Providers bill **per token**, so token count *is* the bill. *Example:* When Alan types a question to a chatbot, his sentence gets chopped into little word-pieces, and he pays a tiny fee for each piece going in and each piece coming back.
- **Input token** — A token in the prompt you *send*. The GPU reads the whole prompt in one parallel pass (the "prefill"), so input tokens are comparatively **cheap and fast**. *Example:* All of Alan's question is read by the model in one quick glance, the way your eye takes in a whole short sentence at once — so the part he *sends* is the bargain half.
- **Output token** — A token the model *generates*. These come out one at a time (the "decode" loop), each needing a full pass over the model, so output tokens cost **3–5× more** and dominate latency (per-token they're ~100–250× slower than input tokens). *Example:* The chatbot writes its reply one word at a time, like someone speaking slowly and thinking between each word — that slow drip is why the *answer* is the pricey, time-consuming half, and why trimming it pays off the most.
- **Premium vs cheap model** — A flagship LLM (e.g. GPT-4-class) is smart but expensive; a budget model is weaker but **15–50× cheaper** per token. Many tasks (classification, extraction, simple Q&A) don't need the flagship. *Example:* Asking the genius professor every trivial question is a waste of money when a sharp teaching assistant could have answered most of them for pennies.
- **LLM proxy / middleware** — A software layer placed **between your app and the provider** that intercepts every request and transparently applies optimizations before forwarding it. (Middleware = code that sits in the request path and pre-processes traffic, like Express/FastAPI middleware.) *Example:* Instead of Alan's app phoning the model directly, a clever receptionist sits in the middle, looks at each question first, and decides how to handle it cheaply before passing it on.
- **Context management (context compression)** — Trimming or summarizing the **conversation history and retrieved documents** stuffed into the prompt *before sending*, so you spend input tokens only on what actually matters. *Example:* Rather than re-reading Alan the entire transcript of every past chat before each new reply, the receptionist keeps a short summary of what's relevant and throws away the rest — far fewer pieces to pay for going in.
- **Model routing (model selection)** — Inspecting each query and **sending easy ones to the cheap model, hard ones to the premium model** (sometimes letting the cheap model answer first and only escalating if a verifier isn't satisfied). *Example:* The receptionist reads the question, and if it's simple, sends it to the cheap teaching assistant; only the genuinely hard ones get escalated to the expensive professor.
- **Semantic caching** — A cache that stores past *question→answer* pairs and serves a stored answer when a **new question means the same thing** (matched by embedding similarity, not exact text). It skips the model call entirely — the cheapest possible request. *Example:* Chloe asks "How do I reset my password?" and later Alan asks "I forgot my password, what now?" — the receptionist recognizes these *mean the same thing* and hands back the answer it already has, with no professor consulted at all.
- **Prompt (prefix) caching** — A *provider-side* cache that reuses the GPU's internal work (the **KV cache**, see [[kv-cache-key-value-cache]]) for a **repeated leading chunk** of the prompt — a system prompt or shared document — so the unchanged prefix isn't recomputed each call. Complements semantic caching rather than replacing it. *Example:* Every one of Alan's questions starts with the same long "You are a helpful tutor…" preamble; the provider remembers the work it already did on that preamble instead of re-reading it from scratch every single time.
- **LLM Token Saving Strategies** — The combined discipline of pulling all three proxy levers (caching + context compression + routing) **plus** prioritizing output-token reduction, to minimize cost and latency without hurting answer quality. *Example:* Put the smart receptionist, the short summaries, the cheap-vs-professor sorting, and the "keep answers short" rule together, and Alan's app gives the same quality answers for a fraction of the price — that whole playbook is the strategy.

### How these terms are related
Read this as a cause-and-effect chain — each step forces the next:

1. **Token → the bill is token count.** You pay per token, so reducing cost means reducing tokens (or their price), not vibes.
2. **Token splits into input vs output, and they're not equal.** Input tokens are read in **parallel** (cheap, fast); output tokens are generated **sequentially** (3–5× costlier, far slower). So *which* tokens you cut matters — trimming output is worth more per engineering hour than trimming input.
3. **Same task, different model prices → routing is possible.** A budget model can be 15–50× cheaper, and many queries don't need the flagship — so picking the right model per query saves money for free.
4. **But these optimizations shouldn't live in app code → put a proxy in the middle.** A transparent **LLM proxy / middleware** intercepts every request and applies the savings in one place, so the app stays simple.
5. **The proxy gets three levers.** (a) **Context management** shrinks the *input* of every call before it's sent. (b) **Model routing** sends each call to the *cheapest sufficient* model. (c) **Semantic caching** kills *redundant* calls entirely (repeated/similar questions).
6. **Add provider-side prompt caching underneath.** **Prompt (prefix) caching** reuses the KV cache for repeated prompt prefixes, cutting the cost of the calls that do reach the model.
7. **Together → LLM Token Saving Strategies.** Stack all of it and a real service (the LLMProxy/LLMBridge WhatsApp study) cut cost ~30% from routing alone and 30–50% from context management — without users noticing a quality drop.

**The chain in one line:**
`Token (you pay per piece) → input vs output (output is the expensive half) → cheap vs premium models → LLM proxy → {context compression · model routing · semantic cache} + prompt caching → LLM Token Saving Strategies`

### Concrete example
A minimal proxy that pulls all three levers (at runtime the cache is checked first so a hit skips everything; otherwise compress the input, then route by difficulty) before ever paying for a premium call:

```python
# 1. SEMANTIC CACHE — skip the model entirely if a similar question was answered before
q_vec = embed(user_query)                      # turn the question into a vector
hit = vector_db.search(q_vec, threshold=0.92)  # nearest-neighbor match
if hit:
    return hit.answer                          # 0 output tokens, 0 cost

# 2. CONTEXT MANAGEMENT — build a lean prompt: a 200-token summary of history,
#    not the full 4000-token transcript, so we pay for only the input that matters.
prompt = compress_history(history) + user_query

# 3. MODEL ROUTING — let the cheap model try; only escalate hard queries
draft = cheap_model.complete(prompt)           # 15-50x cheaper per token
if confidence(draft) >= 0.8:
    answer = draft
else:
    answer = premium_model.complete(prompt)    # escalate only when needed

vector_db.add(q_vec, answer)                   # populate the cache for next time
return answer
```

Now picture 100 users hammering this proxy. Every prompt first gets its history **compressed** (context management) so the input stays lean. About **13%** of questions then hit the **semantic cache** (the real LLMProxy number) → zero model cost. Of the rest, most are easy and the **cheap model** handles them; only the genuinely hard ones reach the **premium model**, on top of a cached system-prompt prefix (**prompt caching**). Every term above is doing its job in that one request flow — and because answers are kept short, the precious **output tokens** stay few.

### Where you'll meet it
- **LLMProxy / LLMBridge** (Tufts University, 2024) — the academic proxy with a Model Adapter, Context Manager, and Cache; deployed as a WhatsApp Q&A service for 100+ users in developing regions.
- **Commercial AI gateways** — ProxyLLM, Kong AI Gateway, Portkey, LiteLLM, Cloudflare AI Gateway — all sell caching + routing as a drop-in proxy.
- **GPTCache / Redis Vector Cache** — open-source semantic caching libraries.
- **Provider prompt caching** — Anthropic (Claude), OpenAI, and Google all expose prefix/prompt caching billed at a discount.
- **LLMLingua** (Microsoft) — a prompt-compression tool achieving 5–20× input shrinkage.

### Common confusions
- **Semantic cache vs prompt (prefix) cache** — Semantic caching skips the model call *entirely* when a similar question was seen (app-side, vector match); prompt caching reuses the model's internal **KV cache** for a repeated prompt *prefix* (provider-side). Complementary layers, not alternatives.
- **Input tokens vs output tokens** — Input is read in parallel and cheap; output is generated one token at a time and 3–5× costlier (and far slower). Optimize output first.
- **Model routing vs load balancing** — Routing picks a model by *query difficulty/cost*; load balancing spreads traffic across replicas of the *same* model for throughput.
- **Token saving vs vLLM-style serving** — These strategies cut tokens *before/around* the model (proxy layer); engines like [[vllm]] make each token *cheaper to compute* inside the GPU. Different layers of the same cost problem.

---
**Sources:**
- [LLMBridge / LLMProxy: Reducing Costs to Access LLMs in a Prompt-Centric Internet (Tufts, arXiv 2410.11857)](https://arxiv.org/html/2410.11857v1)
- [LLM Cost Optimization: 8 Strategies That Cut API Spend by 80% (PremAI, 2026)](https://blog.premai.io/llm-cost-optimization-8-strategies-that-cut-api-spend-by-80-2026-guide/)
- [Understanding Input/Output tokens vs Latency Tradeoff (MinusX)](https://minusx.ai/blog/input-vs-output-tokens/)
- [Prefix caching — LLM Inference Handbook (BentoML)](https://bentoml.com/llm/inference-optimization/prefix-caching)
- [Caching for LLMs: Prompt, Semantic, and Invalidation (Brenndoerfer)](https://mbrenndoerfer.com/writing/caching-prompt-semantic-invalidation-hit-rates-llm)
