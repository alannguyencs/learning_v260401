## FlashAttention

**In one sentence:** FlashAttention is an **IO-aware** way to compute the *exact* same attention as a standard transformer, but it never writes the giant N×N attention matrix to slow **GPU memory (VRAM)** — instead it processes attention in small **tiles** that fit in the GPU's tiny fast **on-chip memory (SRAM)**, cutting slow memory traffic and giving a several-times wall-clock speedup.

### Key terminologies
These build on each other; read top to bottom and the last term (FlashAttention) falls out naturally.

- **Token** — The small unit of text an LLM reads and emits — usually a word piece (e.g. `"paging"` → `pag` + `ing`). It's the model's input/output unit, but attention never works on tokens directly, only on the vectors derived from them; generation is a loop that emits one token per step, and a length-**N** sequence is N tokens, so attention's cost grows with N.
- **Attention** — The transformer mechanism by which each token "looks back" at earlier tokens — comparing itself against every other token — to decide what to focus on and generate next. For N tokens that's N×N comparisons (the core source of cost), and each new token needs all earlier tokens' representations.
- **Query / Key / Value (Q, K, V)** — The three float vectors each token is projected into. Attention scores a token's **query** against every **key** (via dot product), softmax-normalizes the scores, then sums the **values** with those weights. (See the key/value-vectors note for the full definition.)
- **Attention matrix (the N×N matrix)** — The intermediate table of every query-key score: row *i*, column *j* = how much token *i* attends to token *j*. For N = 8192 tokens that's ~67 million numbers **per attention head** — huge, and only needed transiently.
- **Quadratic complexity (O(N²))** — Because the attention matrix is N×N, both its compute and the memory to store it grow with the *square* of sequence length. Double the context → 4× the cost. This is why long contexts are expensive.
- **GPU memory / VRAM** — The GPU's main on-board memory (the advertised "40 GB" / "80 GB"), holding the model weights *and* every active request's KV cache. Fast versus CPU RAM but comparatively **slow** versus on-chip SRAM (~1.5–3 TB/s), and limited — when it fills up you must drop requests or shrink the batch, so VRAM is the scarce resource. Hardware folks call it **HBM (High-Bandwidth Memory)**.
- **SRAM (on-chip memory)** — Tiny scratchpad memory physically on the GPU compute cores (~20 MB total). **~10× faster** than VRAM (~19 TB/s) but far too small to hold the whole attention matrix.
- **Memory bandwidth bound (IO-bound)** — When an operation spends most of its wall-clock time *moving data* between VRAM and SRAM rather than doing math. Standard attention is IO-bound: writing/reading the N×N matrix to slow VRAM dominates the runtime.
- **IO-awareness** — Designing the algorithm around *minimizing reads/writes between VRAM and SRAM* (counting memory traffic, not just FLOPs). This is the missing principle FlashAttention adds.
- **Tiling (blocking)** — Splitting Q, K, V into small **blocks** that each fit in SRAM, and looping over block pairs so the attention math happens entirely in fast memory — the N×N matrix is never materialized in HBM.
- **Online softmax** — A streaming way to compute softmax block-by-block: keep a running max and running sum, and rescale the partial result as each new block arrives — so you get the exact softmax without ever holding a full row of scores at once.
- **Recomputation** — Instead of storing the big intermediate matrix for the backward (gradient) pass, FlashAttention re-derives it on the fly from the small saved stats. Trades a little extra compute for a large memory saving.
- **FlashAttention** — The attention kernel that combines tiling + online softmax + recomputation to compute *exact* attention with **linear (O(N))** memory and far fewer VRAM accesses — making it both faster and able to handle much longer sequences.

### How these terms are related
Read this as a cause-and-effect chain — each step forces the next:

1. **Attention → an N×N matrix.** Every token attends to every token, so attention forms an **N×N** score table.
2. **N×N → quadratic blow-up.** That table's size and cost scale as **O(N²)**; long sequences make it enormous.
3. **Big matrix → it lives in VRAM.** Standard attention writes the full N×N matrix out to **GPU memory (VRAM)**, runs softmax over it, then reads it back to multiply by V.
4. **VRAM round-trips → IO-bound.** VRAM is slow, so all that writing and re-reading — not the arithmetic — dominates runtime: attention is **memory-bandwidth bound**.
5. **IO-bound → make it IO-aware.** The fix is to minimize VRAM traffic, i.e. design the kernel to be **IO-aware** and keep work in fast **SRAM**.
6. **SRAM too small → tiling.** SRAM can't hold the whole matrix, so split Q/K/V into **tiles** that fit, and loop over tile pairs computing partial attention in SRAM.
7. **Tiling breaks softmax → online softmax.** Softmax normally needs a whole row at once; processing tiles means you only see part of a row, so use **online softmax** (running max + running sum) to still get the *exact* result.
8. **Backward pass needs the matrix → recomputation.** Rather than store the N×N matrix for gradients, **recompute** it from small saved statistics — keeping memory **linear in N**.
9. **All together → FlashAttention.** Tiling + online softmax + recomputation = exact attention with far fewer VRAM accesses (up to ~9× fewer), **2–7× faster**, and long-context-capable.

**The chain in one line:**
`attention → N×N matrix → O(N²) → stored in slow VRAM → IO-bound → IO-aware → tiling (SRAM) → online softmax → recomputation → FlashAttention (exact, faster, linear memory)`

### Concrete example
Most users never call it directly — it's a drop-in kernel. In PyTorch, the built-in scaled-dot-product attention dispatches to a FlashAttention backend automatically:

```python
import torch
import torch.nn.functional as F

# Q, K, V: (batch, heads, seq_len, head_dim) on a CUDA GPU
q = torch.randn(2, 16, 8192, 64, device="cuda", dtype=torch.float16)
k = torch.randn_like(q)
v = torch.randn_like(q)

# Under the hood this runs the FlashAttention kernel — no N×N matrix
# is ever written to GPU memory (VRAM), even though seq_len = 8192.
out = F.scaled_dot_product_attention(q, k, v)   # (2, 16, 8192, 64)
```

Picture seq_len = 8192. Standard attention would allocate a `(2, 16, 8192, 8192)` score tensor in **GPU memory (VRAM)** — about 2 GB just for the **attention matrix**. FlashAttention instead streams Q/K/V **tiles** through **SRAM**, keeps a running **online-softmax** max/sum, and writes only the small `(…, 8192, 64)` output back — so that 2 GB matrix never exists, and the kernel runs several times faster.

### Where you'll meet it
- **PyTorch** `F.scaled_dot_product_attention` and HuggingFace Transformers (`attn_implementation="flash_attention_2"`).
- **vLLM, TGI, TensorRT-LLM** and most serving stacks use a FlashAttention kernel for the attention compute (alongside PagedAttention for KV-cache storage).
- The original **Dao et al. 2022** paper (Stanford / Tri Dao); later **FlashAttention-2** (better GPU parallelism/work partitioning) and **FlashAttention-3** (Hopper H100-specific: async warp specialization, FP8).
- Anytime someone trains or serves long-context models (32k+ tokens) on NVIDIA GPUs.

### Common confusions
- **FlashAttention vs. PagedAttention** — FlashAttention speeds up the attention *computation* (less VRAM traffic during the math); PagedAttention optimizes how the **KV cache** is *stored* (no fragmentation). Different problems, routinely used together in vLLM.
- **Exact, not approximate** — Unlike sparse/low-rank "efficient attention," FlashAttention computes the *identical* result as standard attention — it's a faster route to the same numbers, not an approximation.
- **It reduces *memory traffic*, not FLOPs** — It does roughly the same arithmetic; the win is doing far fewer slow VRAM reads/writes. (It also lowers peak memory from O(N²) to O(N).)
- **FlashAttention vs. Flash Attention "the feature"** — Here it's the GPU kernel/algorithm, not a UI feature. The name refers to keeping computation in fast on-chip memory ("flash").

---
**Sources:**
- [FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness (Dao et al., arXiv 2205.14135)](https://arxiv.org/abs/2205.14135)
- [FlashAttention paper PDF (arXiv)](https://arxiv.org/pdf/2205.14135)
- [FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning (Tri Dao)](https://arxiv.org/abs/2307.08691)
- [FlashAttention — The Tiling Strategy (HuggingFace blog)](https://huggingface.co/blog/atharv6f/flash-attention-basics)
- [FlashAttention 2 vs 3: H100/H200 speedups, FP8 (Spheron blog, 2026)](https://www.spheron.network/blog/flashattention-2-vs-flashattention-3-h100-h200-guide/)
