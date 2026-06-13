# FlashAttention

Alright, settle in, because today we're going to build up one of the most important pieces of engineering in modern large language models, and I want you to notice that we're not going to start with the fancy name at the end — FlashAttention — we're going to *earn* it. Every term I give you is going to create a problem, and the next term is going to be the fix for that problem. If you follow the chain, the last idea will basically fall into your lap.

So let's start at the very bottom, with the thing the model actually reads: a **token**. A token is the small unit of text a language model takes in and spits out — usually a word piece, not even a whole word. The word `"paging"` might get chopped into `pag` and `ing`, and each of those pieces is a token. Now here's the first thing I want you to internalize: the model never does its real thinking on the token itself. The token is just the doorway. Inside, every token gets turned into vectors, and generation is a loop — one token out per step, then again, then again. So if your sequence is **N** tokens long, that N is going to follow us everywhere, because the cost is going to grow with it.

```
text → tokens → vectors → (the model works on these)
"paging" → pag + ing
```

And what does the model *do* with those vectors? This is **attention**. Attention is the mechanism where every token looks back at the earlier tokens and asks, "which of you matters to me right now?" It compares itself against every other token to decide what to focus on and what to generate next. Now slow down here, because this is where N bites us for the first time. If each of N tokens has to compare itself against all N tokens, that's N times N comparisons. Say that out loud — **N×N** — because that pattern is the seed of every cost problem we're about to hit.

```
each token  ──compares against──>  every token
N tokens  →  N × N comparisons
```

Before we go further, let me name the three vectors attention actually uses, because you'll see them in every diagram for the rest of your life. Each token gets projected into a **query**, a **key**, and a **value** — Q, K, and V. The mechanism is: take a token's query, score it against every other token's key using a dot product, run those scores through softmax so they become nice weights that sum to one, and then take a weighted sum of the values. That's attention in one breath. Query asks the question, keys answer "how relevant am I," values carry the actual content.

```
query ──dot product──> keys  →  softmax → weights  →  weighted sum of values
```

Now, when you do all those query-against-key scores, you don't get a single number — you get a whole table. This is the **attention matrix**, the famous N×N matrix. Row *i*, column *j* tells you how much token *i* attends to token *j*. And I want you to feel how big this gets, not just nod at it. Take N equal to 8192 tokens — a perfectly ordinary context length. That table has about **67 million numbers**. And that's *per attention head*, and a model has many heads. The cruel part is that this enormous table is only needed for a moment, transiently, just to compute the output — and then it's thrown away.

```
attention matrix:  N × N table
row i, col j = how much token i attends to token j
N = 8192  →  ~67 million numbers  (per head)
```

And once you say "N×N," you've already walked into the next idea: **quadratic complexity**, O(N²). Because the matrix is N by N, both the compute to fill it and the memory to hold it grow with the *square* of the sequence length. So here's the rule of thumb that should scare you a little: double the context, and you don't double the cost — you **quadruple** it. That single fact is why long contexts are so expensive, and it's the pressure that's going to drive everything else.

```
context ×2  →  cost ×4     (that's the O(N²) tax)
```

So now we have this giant, briefly-needed table, and we have to ask the very practical question: *where does it physically live?* And to answer that, you need to understand the GPU's memory, because this whole lecture is secretly a story about memory, not about math. The big pool is **GPU memory**, or **VRAM** — that's the "40 gigabyte" or "80 gigabyte" number on the spec sheet. It holds the model weights and every active request's data. It's fast compared to your laptop's RAM, sure, but — and this is the key word — it's **slow** compared to what's coming next, and it's limited. When VRAM fills up, you start dropping requests. The hardware people call it **HBM**, high-bandwidth memory, so don't get thrown when you see that acronym; it's the same thing.

```
VRAM / HBM  →  big (40–80 GB), holds everything, but ~1.5–3 TB/s = "slow"
```

And right next to the compute cores sits something completely different: **SRAM**, the on-chip memory. Think of it as a tiny scratchpad, physically sitting on the GPU's cores — maybe 20 megabytes total. It is roughly **ten times faster** than VRAM. But notice the catch immediately: 20 megabytes. Our attention matrix was gigabytes. So SRAM is blazing fast and hopelessly small — remember that tension, because resolving it is the whole trick.

```
SRAM  →  tiny (~20 MB), on the cores, ~10× FASTER than VRAM
VRAM  →  huge but slow        SRAM  →  fast but tiny
```

Now I can tell you what's actually wrong with standard attention, and it is *not* what most people guess. The problem is not that the arithmetic is slow. The problem is that the operation is **memory-bandwidth bound** — IO-bound. That means it spends most of its wall-clock time just *shuffling data* between slow VRAM and the cores, not doing math. Standard attention writes that whole N×N matrix out to slow VRAM, reads it back to do softmax, writes it again, reads it again to multiply by V. All that round-tripping to slow memory — *that's* what eats the clock. The math is sitting there bored, waiting for data to arrive.

```
standard attention spends its time MOVING the matrix, not computing it
write N×N → VRAM → read → softmax → write → read → multiply...
→ IO-bound
```

So if the bottleneck is memory traffic, then the fix has to be a principle that almost nobody was optimizing for: **IO-awareness**. This is the missing idea that FlashAttention contributes. Instead of only counting FLOPs — floating point operations, the math — you design the algorithm to count and *minimize* the reads and writes between VRAM and SRAM. You optimize for memory traffic. The moment you accept that memory movement is the enemy, the rest of the design writes itself.

```
old goal:  minimize FLOPs (math)
IO-aware:  minimize VRAM↔SRAM traffic (movement)
```

The first thing IO-awareness tells you to do is keep the work in fast SRAM. But we already hit the wall — SRAM is way too small to hold the whole matrix. So you don't hold the whole matrix. You do **tiling**, also called blocking. You chop Q, K, and V into small **blocks** that each fit in SRAM, and you loop over pairs of blocks, computing a little piece of the attention entirely inside fast memory. The huge N×N matrix is *never* assembled in VRAM — it only ever exists as tiny tiles passing through the scratchpad.

```
Q,K,V → small tiles → each fits in SRAM
loop tile-pairs → compute partial attention in SRAM
(the full N×N matrix is never built in VRAM)
```

But the moment you start tiling, you break something, and a sharp student should already feel the discomfort: softmax. Softmax normally needs to see a *whole row* of scores at once, because to normalize it has to know the maximum and the total sum across the entire row. If you're only looking at one tile, you only see *part* of a row. So how can you possibly get the right answer? The fix is **online softmax** — a streaming trick. As each new tile arrives, you keep a running maximum and a running sum, and you rescale the partial result you've accumulated so far to account for the new information. When the last tile has gone by, the math works out to the *exact* same softmax you'd have gotten the old way — you just never had to hold a full row in one place.

```
tile sees only part of a row → softmax can't normalize yet
online softmax: running max + running sum, rescale per tile
→ exact same result, never holds a full row
```

There's one more place the big matrix wants to come back and haunt us: the backward pass, where the model computes gradients to learn. Normally you'd *store* that huge N×N matrix from the forward pass so you can reuse it for the gradients. But storing it puts us right back in O(N²) memory — exactly what we were running from. So FlashAttention does something that sounds wasteful but is actually brilliant: **recomputation**. It throws the matrix away, and during the backward pass it just *re-derives* the needed pieces on the fly from the small statistics it kept. You spend a little extra compute — but remember, compute was never our bottleneck, memory traffic was — and in exchange your memory stays **linear in N** instead of quadratic.

```
backward pass needs the matrix → don't store it (that's O(N²))
recompute it from small saved stats → memory stays O(N)
```

And now — now we've earned the name. Put the three tricks together: **tiling** to keep work in fast SRAM, **online softmax** to keep the result exact across tiles, and **recomputation** to keep memory linear. That combination *is* **FlashAttention** — an attention kernel that computes the *exact* same answer as standard attention, with linear O(N) memory and far fewer trips to slow VRAM. The result is up to around nine times fewer VRAM accesses, roughly two to seven times faster on the clock, and the ability to handle much longer sequences than before.

```
tiling + online softmax + recomputation = FlashAttention
exact answer · O(N) memory · ~9× fewer VRAM reads · 2–7× faster
```

Let me show you how little of this you actually have to touch, because here's the happy ending: you almost never call it by hand. In PyTorch you just write `F.scaled_dot_product_attention(q, k, v)` with your Q, K, and V on a CUDA GPU, and under the hood it dispatches to a FlashAttention kernel automatically. Picture our sequence length of 8192 again. The old way would allocate a score tensor of shape batch-by-heads-by-8192-by-8192 in VRAM — about 2 gigabytes of pure attention matrix, just sitting there. FlashAttention streams the Q, K, and V tiles through SRAM, keeps its running online-softmax max and sum, and writes back only the small output. That 2-gigabyte matrix simply never exists, and the whole thing runs several times faster.

```
F.scaled_dot_product_attention(q, k, v)  → FlashAttention under the hood
seq_len 8192:  old way = ~2 GB matrix in VRAM
               FlashAttention = that 2 GB matrix never exists
```

Now let me leave you with a few things people constantly get tangled, because knowing these is what separates someone who memorized the name from someone who understands it. First, **FlashAttention is not PagedAttention**. They live in the same systems — vLLM uses both — but they solve different problems: FlashAttention speeds up the attention *computation* by cutting VRAM traffic during the math, while PagedAttention optimizes how the **KV cache** is *stored* so it doesn't fragment. Different jobs, often working side by side. Second, and say this one back to yourself: FlashAttention is **exact, not approximate**. Unlike sparse or low-rank "efficient attention" schemes that cut corners, FlashAttention computes the *identical* numbers as standard attention — it's a faster road to the same destination, not a shortcut to a slightly-wrong answer. Third, remember what it actually saves: it reduces **memory traffic, not FLOPs**. It does roughly the same arithmetic; the entire win is doing far fewer slow reads and writes — and as a bonus, dropping peak memory from O(N²) to O(N). And finally, don't confuse this with any "Flash" *feature* in some app's interface — here it's a GPU kernel, and the word "flash" is about keeping the computation in fast on-chip memory.

```
FlashAttention → speeds up the COMPUTE (less VRAM traffic)
PagedAttention → fixes KV-cache STORAGE (no fragmentation)
same system, different jobs
```

You'll meet this everywhere real models get trained or served: PyTorch's scaled-dot-product attention and HuggingFace's `flash_attention_2`, serving stacks like vLLM and TGI and TensorRT-LLM, the original Dao et al. 2022 paper out of Stanford, and its successors — FlashAttention-2 with better GPU work partitioning, and FlashAttention-3 tuned for the H100. Anytime someone runs a long-context model — 32,000 tokens and beyond — on NVIDIA hardware, this is the quiet kernel making it possible. And if you ever forget the whole story, just remember the one-line chain that got us here: attention forces an N×N matrix, the matrix forces O(N²) cost, that cost lands in slow VRAM, slow VRAM makes us IO-bound, being IO-bound makes us IO-aware, IO-awareness gives us tiling in SRAM, tiling forces online softmax, the backward pass forces recomputation — and all of it together is FlashAttention.
