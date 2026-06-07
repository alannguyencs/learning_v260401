# Attention matrix (the N×N matrix)

The intermediate table of every query-key score: row *i*, column *j* = how much token *i* attends to token *j*. For N = 8192 tokens that's ~67 million numbers **per attention head** — huge, and only needed transiently.
