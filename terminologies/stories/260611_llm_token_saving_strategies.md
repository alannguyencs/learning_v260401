# LLM Token Saving Strategies

Alright everyone, settle in, because today we're going to talk about money. Specifically, why your clever little app that calls a large language model can quietly run up a bill that makes your eyes water, and what a handful of well-known tricks do about it. And I want to start at the very bottom, with the smallest thing in the whole system, because once you understand that small thing, everything else is just consequences.

That small thing is the **token**. A **token** is the little chunk of text that a language model reads and writes — usually a word-piece, so the word `"caching"` might get chopped into `cach` and `ing`. Here's the part I need you to burn into your memory: the provider bills you **per token**. The token count *is* the bill. So when Alan types a question into a chatbot, his sentence gets sliced into these little word-pieces, and he pays a tiny fee for every piece going in, and a tiny fee for every piece coming back out. Multiply those tiny fees by a few million requests and you see why we're here.

```
your text  →  tokens (cach + ing + ...)  →  you pay per piece
```

Now, the moment you accept that you pay per token, the very next question should be: are all tokens priced the same? And the answer — this surprises people — is no, not even close. The tokens split into two kinds, and you have to keep them apart in your head. There's the **input token**, which is a token in the prompt you *send*. The model reads your whole prompt in one parallel pass — the folks who build these systems call it the "prefill" — so the **input token** is comparatively cheap and fast. Think of Alan's question being taken in by the model in one quick glance, the way your eye swallows a whole short sentence at once. The part Alan *sends* is the bargain half.

And then there's the other kind, the **output token**, which is a token the model *generates*. And this is where the asymmetry lives. The **output token** does not come out in one glance. The **output token** comes out one at a time, in what's called the "decode" loop, and each single one of them requires a full pass over the entire model. So the **output token** costs roughly three to five times more than an input token, and per token it can be a hundred to two hundred and fifty times *slower*. Picture the chatbot writing its reply one word at a time, like someone speaking slowly and thinking between each word — that slow drip is the expensive, time-consuming half. So when you go looking for savings, trimming the *output* is worth more per hour of your engineering time than trimming the input. Remember that.

```
input token   →  read all at once (prefill)   →  cheap, fast
output token  →  written one by one (decode)  →  3–5× costlier, far slower
```

Okay. Same idea of "not all things are priced equally" applies one level up, to the model itself. You don't have one LLM, you have a choice. There's the **premium** model — the flagship, the GPT-4-class brain — which is brilliant but expensive. And there's the **cheap** model, weaker, but fifteen to fifty times cheaper per token. And here's the thing nobody wants to admit: a huge fraction of the questions you fire at the flagship don't need the flagship at all. Classification, extraction, simple little factual Q&A — a budget model handles those fine. It's like asking the genius professor every trivial question when a sharp teaching assistant could've answered most of them for pennies. So right there you have a second lever: pick the right model for the job.

```
premium model  →  smart, expensive
cheap model    →  weaker, 15–50× cheaper   →  fine for the easy 80%
```

Now, you *could* scatter all these decisions throughout your application code — check the cache here, summarize the history there, pick a model over in this other file. Please don't. The cleaner idea, and the one the whole industry has converged on, is to put a single layer in the middle. We call it an **LLM proxy**, or **middleware**. The **LLM proxy** sits between your app and the model provider, it intercepts every request, and it transparently applies all the savings before forwarding the call. If you've used Express or FastAPI middleware — code that sits in the request path and pre-processes traffic — it's exactly that idea. Instead of Alan's app phoning the model directly, a clever receptionist now sits in the middle, looks at each question first, and decides how to handle it cheaply before passing it on. And once you've got that receptionist, you can hand it levers to pull.

```
Alan's app  →  [ LLM proxy / receptionist ]  →  model provider
```

So let's hand it the first lever. The first thing the receptionist does is **context management**, sometimes called context compression. The idea: before sending anything, you trim or summarize the conversation history and the retrieved documents that get stuffed into the prompt, so you only spend input tokens on what actually matters. Rather than re-reading Alan the entire transcript of every past chat before every single new reply, the receptionist keeps a short summary of what's relevant and throws the rest away. **Context management** is attacking the *input* side — fewer pieces to pay for going in.

```
full 4000-token transcript  →  context management  →  200-token summary
```

The second lever is **model routing**, also called model selection, and this is where that premium-versus-cheap choice from earlier finally pays off. **Model routing** means the receptionist inspects each query and sends the easy ones to the cheap model and the hard ones to the premium model. A common refinement: let the cheap model answer *first*, and only escalate to the expensive one if some verifier isn't satisfied with the draft. So the receptionist reads the question, and if it's simple, it goes to the cheap teaching assistant; only the genuinely hard ones get bumped up to the expensive professor. **Model routing** doesn't reduce token count — it reduces token *price*.

```
query  →  easy?  →  cheap model
       →  hard?  →  premium model
```

The third lever is the most dramatic one, because it doesn't make the call cheaper — it skips the call *entirely*. This is **semantic caching**. A **semantic cache** stores past question-and-answer pairs, and when a new question comes in that *means the same thing* as one it's seen before, it just hands back the stored answer. And I want you to notice the word "means" — this is not exact text matching. The **semantic cache** matches on meaning, using embedding similarity. So Chloe asks "How do I reset my password?" and later Alan asks "I forgot my password, what now?" — different words, same intent — and the receptionist recognizes that these *mean the same thing* and returns the answer it already has, with no professor and no teaching assistant consulted at all. Zero output tokens, zero cost. That's the cheapest possible request: the one you never make.

```
"reset my password?"      ┐
                          ├─ same meaning  →  serve stored answer, skip the model
"forgot password, help?"  ┘
```

Now there's one more cache I want to put next to that, because students mix these two up constantly, and the distinction matters. The semantic cache we just met lives in *your* layer, on the app side, and it skips the whole model call. But there's also **prompt caching**, sometimes called prefix caching, and the **prompt cache** lives on the *provider's* side. The **prompt cache** reuses the model's own internal work — its KV cache, the per-token key and value vectors it builds during attention — for a repeated leading chunk of the prompt. Think of that long "You are a helpful tutor…" preamble that sits at the front of every one of Alan's questions. Without prompt caching the provider re-reads and re-processes that preamble from scratch every single time. With **prompt caching**, the provider remembers the work it already did on that unchanged prefix and reuses it. So the semantic cache skips the call; the **prompt cache** makes the calls you *do* make cheaper. They're complementary layers, not rivals — and if you want the deeper story on that KV cache the prompt cache is reusing, that's the [[kv-cache-key-value-cache]] note.

```
semantic cache  →  app side     →  skip the model entirely
prompt cache    →  provider side →  reuse work on the repeated prefix
```

So now step back and look at what we've actually built, because *this whole assembled thing* is what we mean by **LLM Token Saving Strategies**. It's the combined discipline: pull all three proxy levers — compress the context, route to the cheapest sufficient model, cache the repeats — and on top of that, keep prioritizing output-token reduction because, remember, output is the expensive half. Put the smart receptionist, the short summaries, the cheap-versus-professor sorting, and the "keep the answers short" rule all together, and Alan's app gives the same-quality answers for a fraction of the price. That playbook, all of it at once, is the strategy.

Let me make it concrete, the way it actually runs for a hundred users hammering one proxy. A request comes in. The very first thing — at runtime, before anything expensive — the receptionist checks the **semantic cache**, because a hit there means it can skip everything else; and in the real LLMProxy deployment, about thirteen percent of questions hit that cache for zero model cost. If there's no hit, the receptionist does its **context management**, building a lean prompt — say a two-hundred-token summary of history instead of the full four-thousand-token transcript. Then **model routing** kicks in: let the cheap model take a swing, and only if its draft isn't confident enough does the request get escalated to the premium model — which itself is sitting on a cached system-prompt prefix thanks to **prompt caching**. Whatever answer comes back gets dropped into the cache for next time. Every single term we've talked about is doing its job inside that one request flow, and because the answers are kept short, those precious output tokens stay few.

```
request →  semantic cache hit?  →  yes: done (skip everything)
                                →  no: compress context  →  route cheap/premium  →  cache result
```

And this isn't a chalkboard fantasy — let me leave you with where you'll actually run into it. The academic version is **LLMProxy**, also called LLMBridge, out of Tufts in 2024, built from exactly these pieces — a model adapter for routing, a context manager, and a cache — and deployed as a real WhatsApp Q&A service for over a hundred users in developing regions. In their study, model routing alone cut cost by around thirty percent, and context management cut it by thirty to fifty percent, with users none the wiser. On the commercial side you'll see the same pattern sold as a drop-in proxy by AI gateways like Kong, Portkey, LiteLLM, and Cloudflare's AI Gateway. The semantic-cache piece shows up as open-source libraries like GPTCache and Redis Vector Cache. The prompt-caching piece is offered directly by Anthropic, OpenAI, and Google, billed at a discount. And the context-compression piece has tools of its own, like Microsoft's LLMLingua, which can shrink an input five to twenty times.

Two last warnings, the confusions that trip people up. First, don't conflate the semantic cache with the prompt cache — semantic caching skips the model call entirely on the app side, prompt caching reuses the KV cache for a repeated prefix on the provider side; complementary, not interchangeable. Second, don't confuse **model routing** with load balancing — routing picks a model by the query's *difficulty and cost*, while load balancing just spreads traffic across replicas of the *same* model for throughput. Different jobs. And keep one boundary clear in your mind: everything we did today happens *around* the model, in the proxy layer, cutting tokens before they're ever spent — which is a different layer from engines like [[vllm]] that make each token *cheaper to compute* inside the GPU. Same war on cost, different battlefield. Get the proxy layer right first, because the cheapest token, as always, is the one you never send.
