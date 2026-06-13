# Token

- The small unit of text an LLM reads and emits — usually a word piece (e.g. `"paging"` → `pag` + `ing`). It's the model's input/output unit, but attention never works on tokens directly, only on the vectors derived from them; generation is a loop that emits one token per step, and a length-**N** sequence is N tokens, so attention's cost grows with N.
- The small chunk of text an LLM reads and writes — usually a word-piece (e.g. `"caching"` → `cach` + `ing`). Providers bill **per token**, so token count *is* the bill. *Example:* When Alan types a question to a chatbot, his sentence gets chopped into little word-pieces, and he pays a tiny fee for each piece going in and each piece coming back.
