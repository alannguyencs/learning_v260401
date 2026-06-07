# Tiling (blocking)

Splitting Q, K, V into small **blocks** that each fit in SRAM, and looping over block pairs so the attention math happens entirely in fast memory — the N×N matrix is never materialized in HBM.
