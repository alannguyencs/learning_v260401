# FlashAttention

The attention kernel that combines tiling + online softmax + recomputation to compute *exact* attention with **linear (O(N))** memory and far fewer VRAM accesses — making it both faster and able to handle much longer sequences.
