# Query / Key / Value (Q, K, V)

The three float vectors each token is projected into. Attention scores a token's **query** against every **key** (via dot product), softmax-normalizes the scores, then sums the **values** with those weights. (See the key/value-vectors note for the full definition.)
