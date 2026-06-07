# Fragmentation

When chunks of memory are allocated and freed in different sizes over time, the free space breaks into gaps too small to reuse. Total free memory looks large, but no single **contiguous** block is big enough — so capacity is wasted.
