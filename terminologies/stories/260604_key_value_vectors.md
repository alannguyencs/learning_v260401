# Key / Value vectors

Alright everyone, settle in, because today we're going to take apart one of the most quietly misunderstood pieces of a transformer. By the end of this hour I want you to be able to say, without flinching, exactly what a **key** is and what a **value** is inside attention — and, just as importantly, what they are *not*. So let me start with the headline, the thing I want stuck in your head before we earn it: inside attention, every token gets turned into three vectors of plain floating-point numbers — a **query**, a **key**, and a **value**. The key is the token's "matchable handle," the part that gets compared against. The value is the "payload," the actual information the token hands over once it's been matched. Both of those are just lists of numbers. Neither of them is a token. Hold onto that last sentence; half the confusion in this topic comes from forgetting it.

Now, the only honest way to understand what a key and a value are is to walk the whole road from raw text to attention output, because each step on that road exists *because* the previous step left a problem unsolved. So let's start where the model starts: with a **token**. A token is the little chunk of text the model actually reads and emits — usually a word piece, not a whole word. The word `"paging"`, for instance, gets chopped into `pag` and `ing`. That's the model's unit of input and output: it reads a sequence of these and, when it generates, it spits out one token per step in a loop. And here's a detail worth flagging right at the start, because it'll haunt us later — a sequence of length **N** is N tokens, and attention's cost grows with N. But notice straight away: attention never actually does math on the token *text* itself. It works on numbers derived from the token. So our very first job is to get away from text and into numbers.

```
token "pag"  →  (still just text — attention can't use this yet)
```

The first move toward numbers is the **token ID**. Every token string — `"pag"`, `"ing"` — gets mapped to a unique integer through a fixed dictionary we call the **vocabulary**, which has something like 128,000 entries. So `"pag"` might become `8472`. And I want you to see this for what it plainly is: a hash-map lookup. Nothing clever, no learning, no arithmetic. It's the *last* moment in the entire pipeline where the actual characters matter. After this step, the model has forgotten the letters entirely — it sees the integer `8472` and that's all.

```
"pag"  ──vocabulary lookup──>  8472     (the last time text matters)
```

But an integer ID still isn't something you can do meaningful math with — `8472` is just a name, a row number, it doesn't *mean* anything numerically. So the next step turns that ID into the model's real currency: an **embedding**. An embedding is a float vector — maybe 512 numbers long, maybe 4096 — that stands for the token's meaning. And here's the part students always overcomplicate: getting from the ID to the embedding is *not* a computation. The model keeps a big embedding matrix `E`, with one row per vocabulary entry, so its shape is roughly `vocab_size × d_model`. The token ID is simply the row number. `embedding = E[8472]` just means "go fetch row 8472." That's array indexing, pure retrieval. Now, one important aside, because it separates embeddings from the keys and values we're heading toward: the rows of `E` are **learned parameters** — they get nudged by gradient descent during training and then they sit there as stored weights. Keep that contrast in your back pocket, because keys and values, as we'll see, are *not* stored — they're recomputed on the fly.

```
8472  ──index row of E──>  [0.2, -1.1, 0.4, …]     (a lookup, not a calculation)
```

So now we finally have what attention wants: a **vector of floats**. Let me make sure that phrase is concrete for you — it's just an ordered list of real numbers, like `[0.2, -1.1, 0.4, …]`. And here's the thing I need you to internalize: the query, the key, and the value are *all* vectors of exactly this kind. When I say "the key," I do not mean the word, I do not mean the ID — I mean a list of floats. Say it back to yourself: the key is a vector.

Good. Now we have one embedding per token, and we want three different vectors out of it — the query, the key, the value. Where do those come from? From three **projection matrices**, which we call `W_Q`, `W_K`, and `W_V`. These are learned weight matrices — "learned" again meaning adjusted during training by gradient descent. You take the token's embedding and multiply it by each of the three matrices, and out come the three vectors. Same embedding goes in; three different vectors come out, because the three matrices pull out three different aspects of it.

```
embedding ──×W_Q──> query
          ──×W_K──> key
          ──×W_V──> value     (one embedding, three projections)
```

Let me give you each of the three with a picture you won't forget, because the roles are the whole point. Think of a library catalog. The **query** is `q = W_Q · embedding` — it's the "what am I looking for?" vector, the request made by the token currently doing the looking. It's like typing **"books about space"** into the catalog. The **key** is `k = W_K · embedding` — the "what do I offer, to be matched against?" vector. It's like the **topic label printed on each book's spine**: "Astronomy," "Cooking." When you search, the catalog checks your request against those labels. And the **value** is `v = W_V · embedding` — the "what do I actually contribute if I get matched?" vector. That's like the **actual contents of the book** you carry home once its label matched your search. So already you can feel the division of labor: the key is the label you match against, the value is the goods you take away.

```
query  →  "books about space"   (the request)
key    →  spine label "Astronomy"   (what you match against)
value  →  the book's contents   (what you take home)
```

So how does the matching actually happen? Through the **dot product**. You take the query and one key, `q · k`, and that produces a single number measuring how well they align — bigger means a better match. And here's a constraint that falls right out of this: since you're dot-producting them together, the query and the key *must have the same dimension*, which we call `d_k`. You can't dot-product a list of 64 numbers against a list of 80; the shapes have to line up. Remember that — it'll come back when we contrast `d_k` and `d_v`.

```
q · k  →  one number   (bigger = better match;  needs same dimension d_k)
```

Now, doing the dot product gives you one raw score for every past token — a whole pile of numbers of wildly different sizes. That's not yet usable as "attention." We want to turn those scores into a clean distribution: weights that are all positive and that sum to one, so we can read them as "how much of my attention goes to each token." The thing that does that conversion is **softmax**. It takes the raw match scores and squashes them into those nice positive, sum-to-one weights.

```
raw scores  ──softmax──>  weights that sum to 1   ("how much attention each token gets")
```

And now — this is the moment the whole lecture has been building toward — we can finally say cleanly what the **key and value vectors** are *together*. Both are per-token float vectors derived from the token's embedding, never from the token itself. The **key** is the one that gets matched against the query through the dot product; it decides *how much* attention each token receives. The **value** is the payload that the softmax weights are summed over; it decides *what* information actually flows onward. The key answers "how much," the value answers "what." That split is the heart of attention.

Let me now run the entire chain once more, fast, because seeing each step force the next is what makes it stick. Token becomes token ID through the vocabulary — a hash-map lookup, the last place text matters. The token ID becomes an embedding by indexing row `E[id]` — a lookup, not a calculation, because attention needs numbers, not text. The embedding gets multiplied by the three learned matrices `W_Q`, `W_K`, `W_V` to produce the query, key, and value — three float vectors from the *same* embedding. The current token's query is dot-producted against every past token's key to get a raw match score each — and that's exactly why `q` and `k` share dimension `d_k`. Those scores get divided by `√d_k`, just to keep them numerically stable, and then softmaxed into weights that sum to one. And finally the output for the current position is the **weighted sum of the value vectors**, `z = Σ αⱼ · vⱼ`. The key decided how much; the value decided what.

```
token → ID → embedding → (W_K, W_V) → key + value → q·k → softmax → Σ weight·value → output
```

Here's a question a sharp student always asks at this point: why two separate vectors? Why not just one? And the answer is genuinely the cleanest justification in the whole architecture. Matching and retrieving are *different jobs*. Asking "is this token a location word?" is a different operation from answering "here's the location information I carry." Because the jobs differ, the model gives them separate projections — separate matrices, separate vectors. One is the index you search by; the other is the payload you pull out. And because they're independent, the value is even allowed to have a *different* dimension, `d_v`, from the key's `d_k`. The key and query are chained together by the dot product so they must match in size; the value is off doing its own thing, so its size just sets how big the output is.

```
matching  →  key   (used in q·k,  dimension d_k)
retrieving → value  (summed by weights,  dimension d_v — can differ)
```

Let me ground all of this in a tiny piece of code, narrated rather than read line by line. Picture your token embeddings stacked up as `x`, one float vector per token. You've got your three learned matrices `Wq`, `Wk`, `Wv`. You multiply `x` by each: `Q = x @ Wq` gives your queries, `K = x @ Wk` gives your keys — and notice the keys exist *only to be matched against* — and `V = x @ Wv` gives your values, which exist *only to be summed*. Then you compute `scores = Q @ K.transpose / d_k**0.5` — that's every query dot-producted with every key, scaled for stability. You softmax those scores so each row sums to one, and finally `out = weights @ V` blends the value vectors according to those weights. That's a full single-head self-attention, and you can see the key and the value doing their two separate jobs in plain sight.

Make it even more concrete with one phrase: `"The cat sat on the ___"`, and look at the token `"on"`. Its key, `K["on"]`, gets matched against the current query; if it scores high, then its value, `V["on"]` — which carries something like "a surface or location comes next" — dominates the blended output, and that nudges the model toward predicting `"mat"`. And here's the punchline that ties the whole hour together: both `K["on"]` and `V["on"]` are just rows of floats. The word `"on"` itself never enters the arithmetic. It showed up once at the very beginning, to become an embedding, and it'll show up once at the very end, as a next-token probability — but in between, it's numbers all the way down.

Now let me leave you with where you'll actually run into this, and the traps to watch for. You will meet Q/K/V in **every transformer** you ever touch — GPT, Llama, BERT, T5, ViT — it's the beating heart of the attention block. You'll meet it again in the **KV cache**: at generation time, models store each past token's key and value vectors — the *vectors*, not the tokens — so they don't have to recompute them every single step, and that storage is exactly what systems like `PagedAttention` and vLLM are built to optimize. And you'll meet it in **multi-head attention**, where each "head" gets its own `W_Q`, `W_K`, `W_V`, so a single token ends up with several key/value pairs, one per head.

```
KV cache  →  store past keys + values (the vectors), skip recomputation
```

And finally the confusions I want to vaccinate you against. First and loudest: **"the key is the token" — no.** The key is a float vector computed from the token's embedding. The token only appears at the very start and the very end. Second, **key versus value**: same sort of shape, opposite roles — the key is what you *match against*, used in `q·k`; the value is what you *get back*, summed by the weights. One is the index, the other is the payload. Third, **query versus key**: a query is "what I'm looking for," a key is "what I offer to be found by" — and in self-attention every token produces all three, whereas in cross-attention the queries come from one sequence and the keys and values from another. And last, **`d_k` versus `d_v`**: query and key must share `d_k` because they're dot-producted together, but the value's dimension `d_v` is free and just sets the output size. Get those four straight and you genuinely understand attention's core. That's where we'll stop today.
