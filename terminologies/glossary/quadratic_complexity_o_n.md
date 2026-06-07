# Quadratic complexity (O(N²))

Because the attention matrix is N×N, both its compute and the memory to store it grow with the *square* of sequence length. Double the context → 4× the cost. This is why long contexts are expensive.
