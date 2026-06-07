# Memory bandwidth bound (IO-bound)

When an operation spends most of its wall-clock time *moving data* between VRAM and SRAM rather than doing math. Standard attention is IO-bound: writing/reading the N×N matrix to slow VRAM dominates the runtime.
