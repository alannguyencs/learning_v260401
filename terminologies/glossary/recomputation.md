# Recomputation

Instead of storing the big intermediate matrix for the backward (gradient) pass, FlashAttention re-derives it on the fly from the small saved stats. Trades a little extra compute for a large memory saving.
