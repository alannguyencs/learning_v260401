# PagedAttention

vLLM's attention implementation that splits each sequence's KV cache into fixed-size **blocks (pages)**, stores them wherever VRAM has room, and uses a block table (a page table) to find them — eliminating fragmentation.
