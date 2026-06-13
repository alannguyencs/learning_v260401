# Output token

A token the model *generates*. These come out one at a time (the "decode" loop), each needing a full pass over the model, so output tokens cost **3–5× more** and dominate latency (per-token they're ~100–250× slower than input tokens). *Example:* The chatbot writes its reply one word at a time, like someone speaking slowly and thinking between each word — that slow drip is why the *answer* is the pricey, time-consuming half, and why trimming it pays off the most.
