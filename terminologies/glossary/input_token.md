# Input token

A token in the prompt you *send*. The GPU reads the whole prompt in one parallel pass (the "prefill"), so input tokens are comparatively **cheap and fast**. *Example:* All of Alan's question is read by the model in one quick glance, the way your eye takes in a whole short sentence at once — so the part he *sends* is the bargain half.
