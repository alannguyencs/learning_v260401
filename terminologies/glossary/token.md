# Token

The small unit of text an LLM reads and emits — usually a word piece (e.g. `"paging"` → `pag` + `ing`). It's the model's input/output unit, but attention never works on tokens directly, only on the vectors derived from them; generation is a loop that emits one token per step, and a length-**N** sequence is N tokens, so attention's cost grows with N.
