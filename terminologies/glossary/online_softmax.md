# Online softmax

A streaming way to compute softmax block-by-block: keep a running max and running sum, and rescale the partial result as each new block arrives — so you get the exact softmax without ever holding a full row of scores at once.
